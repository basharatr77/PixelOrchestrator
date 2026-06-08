import asyncio
from collections import defaultdict, deque
import hashlib

class IntelligentControlBroker:
    def __init__(self, partitions=3):
        self.partitions = partitions
        self.topics = defaultdict(lambda: [deque() for _ in range(partitions)])
        self.subscribers = defaultdict(list)

        self.offsets = defaultdict(int)
        self.lag = defaultdict(int)

    def _partition(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.partitions

    def publish(self, topic, event):
        key = event["data"].get("id", "default")
        p = self._partition(key)

        event["_offset"] = self.offsets[topic]
        self.offsets[topic] += 1

        self.topics[topic][p].append(event)

        print(f"[INTEL BROKER] {topic} → P{p} | offset={event['_offset']}")

    def subscribe(self, group_id, consumer_id, handler):
        self.subscribers[group_id].append({
            "id": consumer_id,
            "handler": handler,
            "processed": 0
        })

    async def start(self, delay=0.2):
        while True:
            for topic, partitions in self.topics.items():

                for p_id, queue in enumerate(partitions):
                    if not queue:
                        continue

                    event = queue.popleft()

                    for group_id, consumers in self.subscribers.items():
                        for c in consumers:

                            try:
                                await c["handler"](event)
                                c["processed"] += 1

                                self.lag[c["id"]] = event["_offset"]

                            except Exception as e:
                                print("[INTEL ERROR]", e)

            await asyncio.sleep(delay)
