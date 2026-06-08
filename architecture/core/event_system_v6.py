import asyncio
from collections import defaultdict

from architecture.storage.wal_store import WALStore
from architecture.core.autoscaling_workers import AutoScalingWorkers

class EventSystemV6:
    def __init__(self):
        self.topics = defaultdict(list)
        self.subscribers = defaultdict(list)

        self.wal = WALStore()
        self.workers = AutoScalingWorkers()

    def publish(self, topic, event):
        self.wal.append({"topic": topic, "event": event})
        self.topics[topic].append(event)

    def subscribe(self, group, handler):
        self.subscribers[group].append(handler)

    async def start(self):
        asyncio.create_task(self.workers.run())

        while True:
            for topic, events in self.topics.items():
                while events:
                    event = events.pop(0)

                    for group, handlers in self.subscribers.items():
                        for h in handlers:
                            self.workers.submit(event)
                            await h(event)

            await asyncio.sleep(0.1)
