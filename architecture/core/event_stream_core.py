import asyncio
import time
from collections import defaultdict, deque

class EventStreamCore:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.subscribers = defaultdict(list)
        self.event_log = deque(maxlen=1000)
        self.running = False

    async def publish(self, event_type, data):
        event = {
            "type": event_type,
            "data": data,
            "ts": int(time.time())
        }

        self.event_log.append(event)
        await self.queue.put(event)

        if event_type in self.subscribers:
            for cb in self.subscribers[event_type]:
                cb(event)

    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    async def _worker(self):
        while self.running:
            event = await self.queue.get()
            # stream processing hook (future AI layer)
            print(f"[STREAM] {event}")

    async def start(self):
        self.running = True
        asyncio.create_task(self._worker())
        print("[EVENT_STREAM] CORE STARTED")

    async def stop(self):
        self.running = False
        print("[EVENT_STREAM] STOPPED")

    def replay(self, limit=10):
        return list(self.event_log)[-limit:]
