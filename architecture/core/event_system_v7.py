import asyncio
from collections import defaultdict

from architecture.storage.wal_store import WALStore
from architecture.core.partition_router import PartitionRouter
from architecture.core.parallel_workers import ParallelWorkers

class EventSystemV7:
    def __init__(self):
        self.router = PartitionRouter()
        self.wal = WALStore()

        self.topics = defaultdict(list)
        self.subscribers = defaultdict(list)

        self.workers = ParallelWorkers()

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

                    # send to worker pool (parallel execution)
                    await self.workers.submit(event)

                    # fanout
                    for handlers in self.subscribers.values():
                        for h in handlers:
                            asyncio.create_task(h(event))

            await asyncio.sleep(0.05)
