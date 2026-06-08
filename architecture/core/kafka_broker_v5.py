import asyncio
from collections import defaultdict, deque
import hashlib

from architecture.core.control_plane_v5 import ControlPlaneV5
from architecture.core.lease_manager import LeaseManager
from architecture.storage.commit_log import CommitLog

class KafkaBrokerV5:
    def __init__(self, partitions=3):
        self.partitions = partitions
        self.topics = defaultdict(lambda: [deque() for _ in range(partitions)])
        self.subscribers = defaultdict(list)

        self.cp = ControlPlaneV5()
        self.leases = LeaseManager()
        self.commit_log = CommitLog()

        self.offset = defaultdict(int)

    def _partition(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.partitions

    def heartbeat(self, consumer_id):
        self.cp.heartbeat(consumer_id)

    def subscribe(self, group_id, consumer_id, topic, handler):
        self.subscribers[topic].append({
            "id": consumer_id,
            "handler": handler,
            "group": group_id
        })

        print(f"[V5] {consumer_id} joined {group_id}")

    def publish(self, topic, event):
        offset = self.offset[topic]
        self.offset[topic] += 1

        event["_offset"] = offset

        p = self._partition(event["data"]["id"])
        self.topics[topic][p].append(event)

        self.commit_log.append({"topic": topic, "event": event})

        print(f"[V5] {topic} → P{p} | offset={offset}")

    async def _rebalance(self, topic):
        active = self.cp.active()

        for p in range(self.partitions):
            if active:
                self.leases.acquire(p, active[p % len(active)])

    async def start(self, delay=0.2):
        while True:
            for topic, partitions in self.topics.items():

                await self._rebalance(topic)

                for p_id, queue in enumerate(partitions):
                    owner = self.leases.owner(p_id)

                    if not queue or not owner:
                        continue

                    event = queue.popleft()

                    for sub in self.subscribers[topic]:
                        if sub["id"] != owner:
                            continue

                        try:
                            await sub["handler"](event)
                        except Exception as e:
                            print("[V5 ERROR]", e)

            await asyncio.sleep(delay)
