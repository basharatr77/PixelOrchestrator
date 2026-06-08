import asyncio
from collections import defaultdict, deque

from architecture.core.partition_router import PartitionRouter
from architecture.storage.wal_store import WALStore
from architecture.core.parallel_workers import ParallelWorkers

class EventSystemV8:
    def __init__(self):
        self.router = PartitionRouter()
        self.wal = WALStore()

        self.topics = defaultdict(lambda: defaultdict(deque))
        self.subscribers = defaultdict(list)

        self.workers = ParallelWorkers()

    def publish(self, topic, event):
        key = event["id"]
        partition = self.router.route(key)

        self.wal.append({
            "topic": topic,
            "partition": partition,
            "event": event
        })

        self.topics[topic][partition].append(event)

    def subscribe(self, group, handler):
        self.subscribers[group].append(handler)

    async def start(self):
        asyncio.create_task(self.workers.run())

        while True:
            for topic, partitions in self.topics.items():
                for _, queue in partitions.items():
                    while queue:
                        event = queue.popleft()

                        await self.workers.submit(event)

                        for handlers in self.subscribers.values():
                            for h in handlers:
                                await h(event)

            await asyncio.sleep(0.05)
