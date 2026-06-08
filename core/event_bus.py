<<<<<<< HEAD
import asyncio
from collections import defaultdict
from core.event_dedup import EventDeduplicator
=======
<<<<<<< HEAD
from queue import Queue
>>>>>>> 57b558f (auto update)

class EventBus:

    def __init__(self, store):
        self.store = store
        self.subscribers = defaultdict(list)
        self._publishing = False
        self.dedup = EventDeduplicator()

    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type, data=None):

        if self._publishing:
            return

<<<<<<< HEAD
=======
            for h in self.handlers.get(etype, []):
                try:
                    h(event)
                except Exception as e:
                    print("Handler error:", e)
=======
import asyncio
from collections import defaultdict
from core.event_dedup import EventDeduplicator

class EventBus:

    def __init__(self, store):
        self.store = store
        self.subscribers = defaultdict(list)
        self._publishing = False
        self.dedup = EventDeduplicator()

    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type, data=None):

        if self._publishing:
            return

>>>>>>> 57b558f (auto update)
        # ✅ DEDUP CHECK
        if self.dedup.is_duplicate(event_type, data):
            return

        self._publishing = True

        try:
            self.store.save_event(event_type, data)

            callbacks = self.subscribers.get(event_type, [])

            tasks = []
            for cb in callbacks:
                tasks.append(asyncio.create_task(cb(data)))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        finally:
            self._publishing = False
<<<<<<< HEAD
=======
>>>>>>> 0900c60 (Stable Event-Driven Core: AI engine, workflow, dedup, replay fix, async event bus hardened)
>>>>>>> 57b558f (auto update)
