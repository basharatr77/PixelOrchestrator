"""
Async Transport Layer - Single source of truth for all device communication
"""

import asyncio
import subprocess
import threading
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int
    duration: float

class AsyncTransport:
    """Centralized async transport for ADB/Fastboot/EDL commands."""
    
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
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._pending_commands: Dict[str, asyncio.Future] = {}
        self._command_counter = 0
    
    async def execute_async(self, cmd: List[str], timeout: int = 30) -> CommandResult:
        """Execute command asynchronously with timeout."""
        cmd_id = f"cmd_{self._command_counter}"
        self._command_counter += 1
        
        loop = asyncio.get_event_loop()
        
        try:
            start = time.time()
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                duration = time.time() - start
                
                return CommandResult(
                    success=process.returncode == 0,
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    returncode=process.returncode,
                    duration=duration
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return CommandResult(
                    success=False,
                    stdout="",
                    stderr=f"Timeout after {timeout}s",
                    returncode=-1,
                    duration=timeout
                )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=-1,
                duration=0
            )
    
    def execute_sync(self, cmd: List[str], timeout: int = 30) -> CommandResult:
        """Synchronous wrapper for async execute."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.execute_async(cmd, timeout))
            loop.close()
            return result
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=-1,
                duration=0
            )
    
    async def adb(self, args: List[str], serial: Optional[str] = None, timeout: int = 30) -> CommandResult:
        """Execute ADB command."""
        cmd = ["adb"]
        if serial:
            cmd += ["-s", serial]
        cmd += args
        return await self.execute_async(cmd, timeout)
    
    async def fastboot(self, args: List[str], serial: Optional[str] = None, timeout: int = 30) -> CommandResult:
        """Execute Fastboot command."""
        cmd = ["fastboot"]
        if serial:
            cmd += ["-s", serial]
        cmd += args
        return await self.execute_async(cmd, timeout)

async_transport = AsyncTransport()