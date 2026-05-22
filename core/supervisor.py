"""
Async Task Supervisor – cancellation, timeout, monitoring
"""

import asyncio
from typing import Dict, Optional

class TaskSupervisor:
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, any] = {}

    def create_task(self, coro, name: str, timeout: Optional[float] = None) -> str:
        task = asyncio.create_task(coro)
        self._tasks[name] = task
        if timeout:
            asyncio.create_task(self._timeout_wrapper(name, timeout))
        return name

    async def _timeout_wrapper(self, name: str, timeout: float):
        await asyncio.sleep(timeout)
        if name in self._tasks and not self._tasks[name].done():
            self._tasks[name].cancel()

    async def wait_for(self, name: str, timeout: Optional[float] = None) -> any:
        task = self._tasks.get(name)
        if not task:
            raise ValueError(f"Task {name} not found")
        try:
            result = await asyncio.wait_for(task, timeout)
            self._results[name] = result
            return result
        except asyncio.TimeoutError:
            raise
        finally:
            if name in self._tasks:
                del self._tasks[name]

    def cancel_all(self):
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        self._tasks.clear()
