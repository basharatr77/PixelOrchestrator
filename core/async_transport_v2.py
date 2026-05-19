"""
Async Transport V2 – Pure async I/O with cancellation, retry, and health checks
Replaces subprocess.run with asyncio subprocess
"""

import asyncio
import subprocess
import time
import uuid
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from core.safe_logger import safe_logger


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    duration: float
    command_id: str = ""
    cmd: List[str] = field(default_factory=list)


class CommandStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class PendingCommand:
    """Track a pending command for cancellation."""
    id: str
    cmd: List[str]
    process: Optional[asyncio.subprocess.Process] = None
    status: CommandStatus = CommandStatus.PENDING
    created_at: float = field(default_factory=time.time)


class AsyncTransportV2:
    """
    Async transport layer for ADB and Fastboot commands.
    Features:
    - True async I/O (no blocking threads)
    - Command cancellation
    - Automatic retry
    - Health monitoring
    - Command queuing per device
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._pending_commands: Dict[str, PendingCommand] = {}
        self._device_queues: Dict[str, asyncio.Queue] = {}
        self._running = True
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Start background tasks in a separate thread
        self._start_background_loop()
        
        safe_logger.log_signal.connect(lambda msg: None)
        self.log("Async Transport V2 initialized")
    
    def log(self, msg: str):
        """Thread-safe logging."""
        safe_logger.log(f"[AsyncTransport] {msg}")
    
    def _start_background_loop(self):
        """Start asyncio event loop in background thread."""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        
        # Wait for loop to be created
        while self._loop is None:
            time.sleep(0.01)
        
        # Start health check
        self._health_check_task = asyncio.run_coroutine_threadsafe(
            self._health_check_loop(), self._loop
        )
    
    # ========== CORE EXECUTION ==========
    async def _execute(self, cmd: List[str], timeout: int = 30,
                       cmd_id: Optional[str] = None) -> CommandResult:
        """Execute a command asynchronously with timeout."""
        if cmd_id is None:
            cmd_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        # Track command
        pending = PendingCommand(id=cmd_id, cmd=cmd, status=CommandStatus.RUNNING)
        self._pending_commands[cmd_id] = pending
        
        self.log(f"Executing: {' '.join(cmd)} (id: {cmd_id[:8]})")
        
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            pending.process = process
            
            try:
                # Wait with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                duration = time.time() - start_time
                success = process.returncode == 0
                
                result = CommandResult(
                    success=success,
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    returncode=process.returncode,
                    duration=duration,
                    command_id=cmd_id,
                    cmd=cmd
                )
                
                pending.status = CommandStatus.COMPLETED
                self.log(f"Completed: {' '.join(cmd)} ({duration:.2f}s)")
                return result
                
            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()
                duration = time.time() - start_time
                pending.status = CommandStatus.TIMEOUT
                self.log(f"Timeout: {' '.join(cmd)} after {timeout}s")
                
                return CommandResult(
                    success=False,
                    stdout="",
                    stderr=f"Command timed out after {timeout}s",
                    returncode=-1,
                    duration=duration,
                    command_id=cmd_id,
                    cmd=cmd
                )
                
        except Exception as e:
            duration = time.time() - start_time
            pending.status = CommandStatus.FAILED
            self.log(f"Error: {' '.join(cmd)} - {e}")
            
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=-1,
                duration=duration,
                command_id=cmd_id,
                cmd=cmd
            )
        finally:
            # Clean up
            if cmd_id in self._pending_commands:
                del self._pending_commands[cmd_id]
    
    async def _execute_with_retry(self, cmd: List[str], max_retries: int = 3,
                                   timeout: int = 30) -> CommandResult:
        """Execute command with automatic retry."""
        last_result = None
        for attempt in range(max_retries + 1):
            result = await self._execute(cmd, timeout)
            if result.success:
                return result
            last_result = result
            if attempt < max_retries:
                self.log(f"Retry {attempt + 1}/{max_retries} for: {' '.join(cmd)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return last_result
    
    def cancel_command(self, cmd_id: str) -> bool:
        """Cancel a running command."""
        if cmd_id not in self._pending_commands:
            return False
        
        pending = self._pending_commands[cmd_id]
        if pending.process and pending.status == CommandStatus.RUNNING:
            # Send kill signal
            if self._loop:
                asyncio.run_coroutine_threadsafe(
                    self._kill_process(pending.process), self._loop
                )
            pending.status = CommandStatus.CANCELLED
            self.log(f"Cancelled command: {cmd_id[:8]}")
            return True
        
        return False
    
    async def _kill_process(self, process: asyncio.subprocess.Process):
        """Kill a process."""
        try:
            process.kill()
            await process.wait()
        except:
            pass
    
    # ========== HEALTH CHECK ==========
    async def _health_check_loop(self):
        """Background health check loop."""
        while self._running:
            await asyncio.sleep(30)
            
            # Check for stale commands
            now = time.time()
            stale_threshold = 120  # 2 minutes
            
            for cmd_id, pending in list(self._pending_commands.items()):
                if pending.status == CommandStatus.RUNNING:
                    if now - pending.created_at > stale_threshold:
                        self.log(f"Health check: Cancelling stale command {cmd_id[:8]}")
                        self.cancel_command(cmd_id)
    
    def get_health(self) -> Dict:
        """Get health status of the transport layer."""
        return {
            "pending_commands": len(self._pending_commands),
            "active_commands": sum(1 for p in self._pending_commands.values() 
                                   if p.status == CommandStatus.RUNNING),
            "device_queues": len(self._device_queues)
        }
    
    def recover_pending_commands(self):
        """Recover any orphaned commands."""
        # This would be called by the operation manager's recovery loop
        self.log("Recovering pending commands...")
        for cmd_id, pending in list(self._pending_commands.items()):
            if pending.status == CommandStatus.RUNNING:
                duration = time.time() - pending.created_at
                if duration > 60:
                    self.cancel_command(cmd_id)
    
    # ========== ADB COMMANDS ==========
    async def adb_devices(self) -> CommandResult:
        """Get list of ADB devices."""
        return await self._execute(["adb", "devices"])
    
    async def adb_shell(self, serial: str, command: str, timeout: int = 30) -> CommandResult:
        """Execute shell command on device."""
        return await self._execute(["adb", "-s", serial, "shell", command], timeout)
    
    async def adb_reboot(self, serial: str, target: str = "", timeout: int = 30) -> CommandResult:
        """Reboot device via ADB."""
        cmd = ["adb", "-s", serial, "reboot"]
        if target:
            cmd.append(target)
        return await self._execute(cmd, timeout)
    
    async def adb_install(self, serial: str, apk_path: str, timeout: int = 120) -> CommandResult:
        """Install APK on device."""
        return await self._execute(["adb", "-s", serial, "install", "-r", apk_path], timeout)
    
    async def adb_pull(self, serial: str, remote: str, local: str, timeout: int = 60) -> CommandResult:
        """Pull file from device."""
        return await self._execute(["adb", "-s", serial, "pull", remote, local], timeout)
    
    async def adb_push(self, serial: str, local: str, remote: str, timeout: int = 60) -> CommandResult:
        """Push file to device."""
        return await self._execute(["adb", "-s", serial, "push", local, remote], timeout)
    
    async def take_screenshot(self, serial: str) -> CommandResult:
        """Take screenshot and save locally."""
        filename = f"screenshot_{int(time.time())}.png"
        await self.adb_shell(serial, "screencap /sdcard/screenshot.png")
        result = await self.adb_pull(serial, "/sdcard/screenshot.png", filename)
        await self.adb_shell(serial, "rm /sdcard/screenshot.png")
        return result
    
    # ========== FASTBOOT COMMANDS ==========
    async def fastboot_devices(self) -> CommandResult:
        """Get list of fastboot devices."""
        return await self._execute(["fastboot", "devices"])
    
    async def fastboot_getvar(self, serial: str, var: str, timeout: int = 10) -> CommandResult:
        """Get fastboot variable."""
        return await self._execute(["fastboot", "-s", serial, "getvar", var], timeout)
    
    async def fastboot_getvar_all(self, serial: str, timeout: int = 15) -> CommandResult:
        """Get all fastboot variables."""
        return await self._execute(["fastboot", "-s", serial, "getvar", "all"], timeout)
    
    async def fastboot_reboot(self, serial: str, target: str = "", timeout: int = 30) -> CommandResult:
        """Reboot device via fastboot."""
        cmd = ["fastboot", "-s", serial, "reboot"]
        if target:
            cmd.append(target)
        return await self._execute(cmd, timeout)
    
    async def fastboot_flash(self, serial: str, partition: str, image: str, timeout: int = 120) -> CommandResult:
        """Flash partition via fastboot."""
        return await self._execute(["fastboot", "-s", serial, "flash", partition, image], timeout)
    
    async def fastboot_erase(self, serial: str, partition: str, timeout: int = 60) -> CommandResult:
        """Erase partition via fastboot."""
        return await self._execute(["fastboot", "-s", serial, "erase", partition], timeout)
    
    async def fastboot_unlock(self, serial: str, timeout: int = 30) -> CommandResult:
        """Unlock bootloader."""
        return await self._execute(["fastboot", "-s", serial, "flashing", "unlock"], timeout)
    
    async def fastboot_lock(self, serial: str, timeout: int = 30) -> CommandResult:
        """Lock bootloader."""
        return await self._execute(["fastboot", "-s", serial, "flashing", "lock"], timeout)
    
    async def fastboot_continue(self, serial: str, timeout: int = 10) -> CommandResult:
        """Continue boot."""
        return await self._execute(["fastboot", "-s", serial, "continue"], timeout)
    
    # ========== SYNCHRONOUS WRAPPERS (for compatibility) ==========
    def execute_sync(self, cmd: List[str], timeout: int = 30) -> CommandResult:
        """Synchronous wrapper for async execute."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._execute(cmd, timeout))
            loop.close()
            return result
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=-1,
                duration=0,
                cmd=cmd
            )
    
    def adb_devices_sync(self) -> CommandResult:
        """Synchronous ADB devices."""
        return self.execute_sync(["adb", "devices"])
    
    def stop(self):
        """Stop the transport layer."""
        self._running = False
        self.log("Async Transport V2 stopped")


# Global instance
async_transport_v2 = AsyncTransportV2()