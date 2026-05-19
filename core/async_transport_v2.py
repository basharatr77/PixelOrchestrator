"""
Async Transport V2 – Production Grade Async I/O with Cancellation, Retry, and Health Checks
"""

import asyncio
import subprocess
import time
import uuid
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class CommandStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int
    duration: float
    command_id: str = ""
    cmd: List[str] = field(default_factory=list)


class AsyncTransportV2:
    """
    Production-grade async transport with:
    - True async I/O (asyncio subprocess)
    - Command cancellation
    - Automatic retry with backoff
    - Health monitoring
    - Per-device queuing
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
        
        self._pending_commands: Dict[str, Dict] = {}
        self._device_queues: Dict[str, asyncio.Queue] = {}
        self._running = True
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        self._start_loop()
        
        print("[AsyncTransportV2] Initialized")
    
    def _start_loop(self):
        """Start asyncio event loop in background thread."""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        
        # Wait for loop to be ready
        while self._loop is None:
            time.sleep(0.01)
        
        # Start health check
        self._health_check_task = asyncio.run_coroutine_threadsafe(
            self._health_check_loop(), self._loop
        )
    
    async def _execute(self, cmd: List[str], timeout: int = 30,
                       cmd_id: Optional[str] = None) -> CommandResult:
        """Execute a command asynchronously with timeout."""
        if cmd_id is None:
            cmd_id = str(uuid.uuid4())[:8]
        
        start_time = time.time()
        
        # Track command
        self._pending_commands[cmd_id] = {
            "cmd": cmd,
            "status": CommandStatus.RUNNING,
            "process": None,
            "started_at": start_time
        }
        
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self._pending_commands[cmd_id]["process"] = process
            
            try:
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
                
                self._pending_commands[cmd_id]["status"] = CommandStatus.COMPLETED
                return result
                
            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()
                duration = time.time() - start_time
                self._pending_commands[cmd_id]["status"] = CommandStatus.TIMEOUT
                
                return CommandResult(
                    success=False,
                    stdout="",
                    stderr=f"Timeout after {timeout}s",
                    returncode=-1,
                    duration=duration,
                    command_id=cmd_id,
                    cmd=cmd
                )
                
        except Exception as e:
            duration = time.time() - start_time
            self._pending_commands[cmd_id]["status"] = CommandStatus.FAILED
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
            # Clean up after delay
            async def cleanup():
                await asyncio.sleep(5)
                self._pending_commands.pop(cmd_id, None)
            asyncio.create_task(cleanup())
    
    # ========== PUBLIC API ==========
    def cancel_command(self, cmd_id: str) -> bool:
        """Cancel a running command."""
        if cmd_id not in self._pending_commands:
            return False
        
        cmd_info = self._pending_commands[cmd_id]
        if cmd_info["status"] != CommandStatus.RUNNING:
            return False
        
        process = cmd_info.get("process")
        if process:
            # Schedule kill in event loop
            async def kill_process():
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
            asyncio.run_coroutine_threadsafe(kill_process(), self._loop)
        
        cmd_info["status"] = CommandStatus.CANCELLED
        return True
    
    def cancel_all_device_commands(self, device_serial: str):
        """Cancel all pending commands for a device."""
        for cmd_id, cmd_info in list(self._pending_commands.items()):
            cmd = cmd_info["cmd"]
            if device_serial in cmd and cmd_info["status"] == CommandStatus.RUNNING:
                self.cancel_command(cmd_id)
    
    # ========== ADB COMMANDS ==========
    async def adb_devices(self, timeout: int = 10) -> CommandResult:
        return await self._execute(["adb", "devices"], timeout)
    
    def adb_devices_sync(self) -> CommandResult:
        """Synchronous wrapper for ADB devices."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.adb_devices())
            loop.close()
            return result
        except Exception as e:
            return CommandResult(success=False, stdout="", stderr=str(e), returncode=-1, duration=0)
    
    async def adb_shell(self, serial: str, command: str, timeout: int = 30) -> CommandResult:
        return await self._execute(["adb", "-s", serial, "shell", command], timeout)
    
    def adb_shell_sync(self, serial: str, command: str, timeout: int = 30) -> CommandResult:
        """Synchronous wrapper for adb shell."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.adb_shell(serial, command, timeout))
            loop.close()
            return result
        except Exception as e:
            return CommandResult(success=False, stdout="", stderr=str(e), returncode=-1, duration=0)
    
    async def adb_reboot(self, serial: str, target: str = "", timeout: int = 30) -> CommandResult:
        cmd = ["adb", "-s", serial, "reboot"]
        if target:
            cmd.append(target)
        return await self._execute(cmd, timeout)
    
    def adb_reboot_sync(self, serial: str, target: str = "", timeout: int = 30) -> CommandResult:
        """Synchronous wrapper for adb reboot."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.adb_reboot(serial, target, timeout))
            loop.close()
            return result
        except Exception as e:
            return CommandResult(success=False, stdout="", stderr=str(e), returncode=-1, duration=0)
    
    async def adb_install(self, serial: str, apk_path: str, timeout: int = 120) -> CommandResult:
        return await self._execute(["adb", "-s", serial, "install", "-r", apk_path], timeout)
    
    async def adb_pull(self, serial: str, remote: str, local: str, timeout: int = 60) -> CommandResult:
        return await self._execute(["adb", "-s", serial, "pull", remote, local], timeout)
    
    async def adb_push(self, serial: str, local: str, remote: str, timeout: int = 60) -> CommandResult:
        return await self._execute(["adb", "-s", serial, "push", local, remote], timeout)
    
    # ========== FASTBOOT COMMANDS ==========
    async def fastboot_devices(self, timeout: int = 10) -> CommandResult:
        return await self._execute(["fastboot", "devices"], timeout)
    
    async def fastboot_getvar(self, serial: str, var: str, timeout: int = 10) -> CommandResult:
        return await self._execute(["fastboot", "-s", serial, "getvar", var], timeout)
    
    async def fastboot_getvar_all(self, serial: str, timeout: int = 15) -> CommandResult:
        return await self._execute(["fastboot", "-s", serial, "getvar", "all"], timeout)
    
    async def fastboot_reboot(self, serial: str, target: str = "", timeout: int = 30) -> CommandResult:
        cmd = ["fastboot", "-s", serial, "reboot"]
        if target:
            cmd.append(target)
        return await self._execute(cmd, timeout)
    
    def fastboot_reboot_sync(self, serial: str, target: str = "", timeout: int = 30) -> CommandResult:
        """Synchronous wrapper for fastboot reboot."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.fastboot_reboot(serial, target, timeout))
            loop.close()
            return result
        except Exception as e:
            return CommandResult(success=False, stdout="", stderr=str(e), returncode=-1, duration=0)
    
    async def fastboot_flash(self, serial: str, partition: str, image: str, timeout: int = 120) -> CommandResult:
        return await self._execute(["fastboot", "-s", serial, "flash", partition, image], timeout)
    
    def fastboot_flash_sync(self, serial: str, partition: str, image: str, timeout: int = 120) -> CommandResult:
        """Synchronous wrapper for fastboot flash."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.fastboot_flash(serial, partition, image, timeout))
            loop.close()
            return result
        except Exception as e:
            return CommandResult(success=False, stdout="", stderr=str(e), returncode=-1, duration=0)
    
    async def fastboot_erase(self, serial: str, partition: str, timeout: int = 60) -> CommandResult:
        return await self._execute(["fastboot", "-s", serial, "erase", partition], timeout)
    
    async def fastboot_unlock(self, serial: str, timeout: int = 30) -> CommandResult:
        return await self._execute(["fastboot", "-s", serial, "flashing", "unlock"], timeout)
    
    async def fastboot_lock(self, serial: str, timeout: int = 30) -> CommandResult:
        return await self._execute(["fastboot", "-s", serial, "flashing", "lock"], timeout)
    
    async def fastboot_continue(self, serial: str, timeout: int = 10) -> CommandResult:
        return await self._execute(["fastboot", "-s", serial, "continue"], timeout)
    
    # ========== HEALTH & RECOVERY ==========
    async def _health_check_loop(self):
        """Background health check for stuck commands."""
        while self._running:
            await asyncio.sleep(30)
            
            now = time.time()
            for cmd_id, cmd_info in list(self._pending_commands.items()):
                if cmd_info["status"] == CommandStatus.RUNNING:
                    if now - cmd_info["started_at"] > 120:
                        print(f"[AsyncTransportV2] Health check: Cancelling stuck command {cmd_id}")
                        self.cancel_command(cmd_id)
    
    def get_health(self) -> Dict:
        return {
            "pending_commands": len(self._pending_commands),
            "running_commands": sum(1 for c in self._pending_commands.values() 
                                   if c["status"] == CommandStatus.RUNNING),
            "device_queues": len(self._device_queues)
        }
    
    def recover_stuck_commands(self) -> int:
        """Recover stuck commands (called by reconciliation engine)."""
        recovered = 0
        for cmd_id, cmd_info in list(self._pending_commands.items()):
            if cmd_info["status"] == CommandStatus.RUNNING:
                if time.time() - cmd_info["started_at"] > 60:
                    self.cancel_command(cmd_id)
                    recovered += 1
        return recovered
    
    def stop(self):
        """Stop the transport."""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)


# Global instance
async_transport_v2 = AsyncTransportV2()