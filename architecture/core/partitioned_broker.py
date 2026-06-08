import asyncio
from collections import defaultdict, deque
import hashlib

class PartitionedBroker:
    def __init__(self, partitions=3):
        self.partitions = partitions
        self.topics = defaultdict(lambda: [deque() for _ in range(partitions)])
        self.subscribers = defaultdict(list)

    def _get_partition(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.partitions

    def publish(self, topic, event):
        key = event["data"].get("id", "default")
        partition = self._get_partition(key)

        self.topics[topic][partition].append(event)

        print(f"[PARTITIONED] {topic} → P{partition}")

    def subscribe(self, topic, handler):
        self.subscribers[topic].append(handler)

    async def start(self, delay=0.1):
        while True:
            for topic, partitions in self.topics.items():

                for i, queue in enumerate(partitions):
                    if not queue:
                        continue

                    event = queue.popleft()

                    for handler in self.subscribers[topic]:
                        try:
                            await handler(event)
                        except Exception as e:
                            print("[PARTITION ERROR]", e)

            await asyncio.sleep(delay)
