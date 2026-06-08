import asyncio
from collections import defaultdict, deque
import hashlib

class AckBroker:
    def __init__(self, partitions=3):
        self.partitions = partitions
        self.topics = defaultdict(lambda: [deque() for _ in range(partitions)])

        # consumer → topic → last_ack_offset
        self.acks = defaultdict(lambda: defaultdict(lambda: -1))

        self.subscribers = defaultdict(list)
        self.global_offset = defaultdict(int)

    def _partition(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.partitions

    def publish(self, topic, event):
        key = event["data"].get("id", "default")
        p = self._partition(key)

        offset = self.global_offset[topic]
        self.global_offset[topic] += 1

        event["_offset"] = offset
        self.topics[topic][p].append(event)

        print(f"[ACK BROKER] {topic} → P{p} | offset={offset}")

    def subscribe(self, consumer_id, topic, handler):
        self.subscribers[topic].append({
            "id": consumer_id,
            "handler": handler
        })

    async def start(self, delay=0.1):
        while True:
            for topic, partitions in self.topics.items():

                for queue in partitions:
                    if not queue:
                        continue

                    event = queue.popleft()
                    offset = event["_offset"]

                    for sub in self.subscribers[topic]:
                        cid = sub["id"]

                        # exactly-once check
                        if self.acks[cid][topic] >= offset:
                            continue

                        try:
                            await sub["handler"](event)

                            # ACK update
                            self.acks[cid][topic] = offset

                        except Exception as e:
                            print("[ACK ERROR]", e)

            await asyncio.sleep(delay)
