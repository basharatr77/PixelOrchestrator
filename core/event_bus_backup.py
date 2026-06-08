import asyncio
from collections import defaultdict


class EventBus:

    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type, data=None):

        callbacks = self.subscribers.get(event_type, [])

        for cb in callbacks:

            if asyncio.iscoroutinefunction(cb):
                await cb(data)
            else:
                cb(data)
