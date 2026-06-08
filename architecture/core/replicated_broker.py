import asyncio
from collections import defaultdict
from architecture.core.raft_cluster_v2 import RaftClusterV2
from architecture.core.raft_log import RaftLog

class ReplicatedBroker:
    def __init__(self, nodes):
        self.cluster = RaftClusterV2(nodes)
        self.log = RaftLog()
        self.topics = defaultdict(list)
        self.subscribers = defaultdict(list)

    def subscribe(self, node_id, handler):
        self.subscribers[node_id].append(handler)

    def publish(self, topic, event):
        leader = self.cluster.elect()

        if not leader:
            print("[RAFT] No leader (quorum failed)")
            return

        index = self.log.append({
            "topic": topic,
            "event": event,
            "leader": leader
        })

        self.topics[topic].append(index)

        print(f"[REPLICA] leader={leader} log_index={index}")

    async def start(self):
        while True:
            for topic, indexes in self.topics.items():
                while indexes:
                    idx = indexes.pop(0)
                    entry = self.log.entries[idx]

                    for subs in self.subscribers.values():
                        for h in subs:
                            await h(entry["event"])

            await asyncio.sleep(0.1)
