import asyncio
from collections import defaultdict, deque
from architecture.storage.commit_log import CommitLog
from architecture.core.lag_tracker import LagTracker
import hashlib

class KafkaBrokerV3:
    def __init__(self, partitions=3):
        self.partitions = partitions
        self.topics = defaultdict(lambda: [deque() for _ in range(partitions)])
        self.subscribers = defaultdict(list)

        self.commit_log = CommitLog()
        self.lag_tracker = LagTracker()
        self.offset = defaultdict(int)

    def _partition(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.partitions

    def publish(self, topic, event):
        key = event["data"].get("id", "default")
        p = self._partition(key)

        offset = self.offset[topic]
        self.offset[topic] += 1

        event["_offset"] = offset

        self.topics[topic][p].append(event)
        self.commit_log.append({"topic": topic, "event": event})

        self.lag_tracker.update_latest(topic, offset)

        print(f"[V3 BROKER] {topic} → P{p} | offset={offset}")

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

                        try:
                            await sub["handler"](event)
                            self.lag_tracker.commit(cid, topic, offset)

                        except Exception as e:
                            print("[V3 ERROR]", e)

            await asyncio.sleep(delay)
