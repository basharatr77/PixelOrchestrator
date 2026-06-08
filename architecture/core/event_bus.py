import asyncio
from collections import defaultdict

class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, topic, handler):
        self.subscribers[topic].append(handler)

    async def publish(self, topic, event):
        if topic in self.subscribers:
            for h in self.subscribers[topic]:
                await h(event)
