import asyncio
from collections import defaultdict
from core.event_dedup import EventDeduplicator


class EventBus:

    def __init__(self, store):
        self.store = store
        self.subscribers = defaultdict(list)
        self.dedup = EventDeduplicator()

    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type, data=None, persist=True, dedup=True):

        if dedup and self.dedup.is_duplicate(event_type, data):
            return

        try:
            if persist:
                self.store.save_event(event_type, data)

            callbacks = self.subscribers.get(event_type, [])

            tasks = []
            for cb in callbacks:
                tasks.append(asyncio.create_task(cb(data)))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            print(f"[EVENT BUS] Publish failed: {e}")
