import asyncio
from collections import defaultdict, deque
import hashlib

class ConsumerGroupBroker:
    def __init__(self, partitions=3):
        self.partitions = partitions
        self.topics = defaultdict(lambda: [deque() for _ in range(partitions)])

        self.groups = defaultdict(list)
        self.assignment = {}

    def _get_partition(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.partitions

    def publish(self, topic, event):
        key = event["data"].get("id", "default")
        p = self._get_partition(key)

        self.topics[topic][p].append(event)
        print(f"[GROUP BROKER] {topic} → P{p}")

    def subscribe(self, group_id, consumer_id, topic, handler):
        self.groups[group_id].append({
            "id": consumer_id,
            "handler": handler,
            "topic": topic
        })

        self._rebalance(group_id, topic)

    def _rebalance(self, group_id, topic):
        consumers = [c for c in self.groups[group_id] if c["topic"] == topic]

        for i, consumer in enumerate(consumers):
            self.assignment[(group_id, i)] = consumer

    async def start(self, delay=0.1):
        while True:
            for topic, partitions in self.topics.items():

                for p_id, queue in enumerate(partitions):
                    if not queue:
                        continue

                    event = queue.popleft()

                    for (group_id, idx), consumer in self.assignment.items():
                        if idx % self.partitions == p_id:
                            try:
                                await consumer["handler"](event)
                            except Exception as e:
                                print("[GROUP ERROR]", e)

            await asyncio.sleep(delay)
