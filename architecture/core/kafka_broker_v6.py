import asyncio
from collections import defaultdict, deque

from architecture.core.partition_router import PartitionRouter
from architecture.storage.wal_store import WALStore
from architecture.storage.offset_store import OffsetStore
from architecture.core.lag_tracker_v2 import LagTrackerV2

class KafkaBrokerV6:
    def __init__(self, partitions=3):
        self.router = PartitionRouter(partitions)
        self.wal = WALStore()
        self.offset_store = OffsetStore()
        self.lag = LagTrackerV2()

        self.topics = defaultdict(lambda: defaultdict(deque))
        self.subscribers = defaultdict(list)

        self.partitions = partitions
        self.offset = defaultdict(int)

    def publish(self, topic, event):
        key = event["id"]
        p = self.router.route(key)

        offset = self.offset[topic]
        self.offset[topic] += 1

        event["_offset"] = offset
        event["_partition"] = p

        self.wal.append({"topic": topic, "event": event})

        self.lag.update(topic, offset)

        self.topics[topic][p].append(event)

        print(f"[V6] {topic} P{p} offset={offset}")

    def subscribe(self, consumer_id, topic, handler):
        self.subscribers[topic].append({
            "id": consumer_id,
            "handler": handler
        })

    async def start(self, delay=0.05):
        while True:
            for topic, partitions in self.topics.items():
                for p, queue in partitions.items():

                    while queue:
                        event = queue.popleft()
                        offset = event["_offset"]

                        for sub in self.subscribers[topic]:
                            cid = sub["id"]

                            last = self.offset_store.get(cid, topic)

                            # skip already processed
                            if offset <= last:
                                continue

                            try:
                                await sub["handler"](event)

                                self.offset_store.commit(cid, topic, offset)
                                self.lag.commit(cid, topic, offset)

                            except Exception as e:
                                print("[V6 ERROR]", e)

            await asyncio.sleep(delay)
