import asyncio
from collections import defaultdict, deque
import hashlib

from architecture.storage.commit_log import CommitLog
from architecture.core.lag_tracker import LagTracker
from architecture.storage.idempotency_store import IdempotencyStore

class KafkaBrokerV4:
    def __init__(self, partitions=3):
        self.partitions = partitions
        self.topics = defaultdict(lambda: [deque() for _ in range(partitions)])
        self.subscribers = defaultdict(list)

        self.commit_log = CommitLog()
        self.lag_tracker = LagTracker()
        self.idempotency = IdempotencyStore()

        self.offset = defaultdict(int)

    def publish(self, topic, event):
        offset = self.offset[topic]
        self.offset[topic] += 1

        event["_offset"] = offset
        event["_event_id"] = f"{topic}-{offset}"

        p = int(hashlib.md5(event["data"]["id"].encode()).hexdigest(), 16) % self.partitions

        self.topics[topic][p].append(event)

        self.commit_log.append({"topic": topic, "event": event})
        self.lag_tracker.update_latest(topic, offset)

        print(f"[V4 FIXED] {topic} → P{p} | offset={offset}")

    def subscribe(self, consumer_id, topic, handler):
        self.subscribers[topic].append({
            "id": consumer_id,
            "handler": handler
        })

    async def start(self, delay=0.1):
        while True:
            for topic, partitions in self.topics.items():

                for queue in partitions:

                    batch = []
                    while queue and len(batch) < 10:
                        batch.append(queue.popleft())

                    for event in batch:
                        offset = event["_offset"]

                        for sub in self.subscribers[topic]:
                            cid = sub["id"]
                            eid = event["_event_id"]

                            if self.idempotency.seen(cid, eid):
                                continue

                            try:
                                await sub["handler"](event)

                                self.idempotency.mark(cid, eid)
                                self.lag_tracker.commit(cid, topic, offset)

                            except Exception as e:
                                print("[V4 ERROR]", e)

            await asyncio.sleep(delay)
