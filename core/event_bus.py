"""
Async Event Bus – pure asyncio
"""

import asyncio
from typing import Dict, List, Callable
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    DEVICE_STATE_CHANGE = "device_state_change"
    JOB_CREATED = "job_created"
    JOB_COMPLETED = "job_completed"
    FLASH_START = "flash_start"
    FLASH_PROGRESS = "flash_progress"
    FLASH_END = "flash_end"
    ERROR = "error"
    LOG = "log"

@dataclass
class Event:
    type: EventType
    payload: dict
    source: str = ""

class EventBus:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = {}
            cls._instance._queue = asyncio.Queue()
            cls._instance._running = False
        return cls._instance

    async def start(self):
        self._running = True
        asyncio.create_task(self._dispatch_loop())

    async def _dispatch_loop(self):
        while self._running:
            event = await self._queue.get()
            for cb in self._subscribers.get(event.type, []):
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(event)
                    else:
                        cb(event)
                except Exception as e:
                    print(f"Event callback error: {e}")

    def subscribe(self, event_type: EventType, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def emit(self, event: Event):
        self._queue.put_nowait(event)

    async def stop(self):
        self._running = False

event_bus = EventBus()
