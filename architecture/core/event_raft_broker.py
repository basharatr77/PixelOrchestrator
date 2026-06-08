import asyncio
from collections import defaultdict

from architecture.core.raft_cluster import RaftCluster
from architecture.storage.event_store_v3 import EventStoreV3
from architecture.core.worker_pool import WorkerPool

class EventRaftBroker:
    def __init__(self):
        self.cluster = RaftCluster()
        self.store = EventStoreV3()
        self.workers = WorkerPool(2)

        self.topics = defaultdict(list)
        self.subscribers = defaultdict(list)

    def register_node(self, node_id):
        self.cluster.register(node_id)

    def subscribe(self, node_id, handler):
        self.subscribers[node_id].append(handler)

    def publish(self, topic, event):
        leader = self.cluster.elect_leader()

        if not leader:
            print("[RAFT] No leader")
            return

        event["_leader"] = leader

        self.store.append({"topic": topic, "event": event})
        self.topics[topic].append(event)

        print(f"[RAFT] leader={leader} → {topic}")

    async def start(self):
        asyncio.create_task(self.workers.run())

        while True:
            for topic, events in self.topics.items():
                while events:
                    event = events.pop(0)

                    self.workers.submit(event)

                    for subs in self.subscribers.values():
                        for h in subs:
                            try:
                                await h(event)
                            except Exception as e:
                                print("[RAFT ERROR]", e)

            await asyncio.sleep(0.1)
