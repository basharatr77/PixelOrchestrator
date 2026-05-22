import asyncio
import subprocess
import time
import uuid
import threading
from typing import List, Dict, Optional, Any
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
        self._loop = None
        self._thread = None
        self._start_loop()

    def _start_loop(self):
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        while self._loop is None:
            time.sleep(0.01)

    async def _execute(self, cmd: List[str], timeout: int = 30, cmd_id: str = None) -> CommandResult:
        if cmd_id is None:
            cmd_id = str(uuid.uuid4())[:8]
        start = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                duration = time.time() - start
                return CommandResult(
                    success=process.returncode == 0,
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    returncode=process.returncode,
                    duration=duration,
                    command_id=cmd_id,
                    cmd=cmd
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return CommandResult(
                    success=False,
                    stdout="", stderr=f"Timeout after {timeout}s",
                    returncode=-1, duration=time.time()-start,
                    command_id=cmd_id, cmd=cmd
                )
        except Exception as e:
            return CommandResult(success=False, stdout="", stderr=str(e), returncode=-1, duration=time.time()-start, command_id=cmd_id, cmd=cmd)

    async def execute_command_async(self, cmd: List[str], job_id: str = "", log_callback=None) -> CommandResult:
        """Execute command with optional live log streaming."""
        return await self._execute(cmd, timeout=300, cmd_id=job_id)

    def execute_sync(self, cmd: List[str], timeout: int = 30) -> CommandResult:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._execute(cmd, timeout))
            loop.close()
            return result
        except Exception as e:
            return CommandResult(success=False, stdout="", stderr=str(e), returncode=-1, duration=0, cmd=cmd)

async_transport_v2 = AsyncTransportV2()
