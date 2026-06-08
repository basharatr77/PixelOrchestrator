import asyncio
from collections import defaultdict
from architecture.core.raft_log import RaftLog
from architecture.core.raft_cluster_v2 import RaftClusterV2

class ReplicatedBrokerV3:
    def __init__(self, nodes):
        self.cluster = RaftClusterV2(nodes)
        self.log = RaftLog()

        self.topics = defaultdict(list)
        self.subscribers = defaultdict(list)

        self.leader = None

    def subscribe(self, consumer_id, handler):
        self.subscribers[consumer_id].append(handler)

    def elect_leader(self):
        if not self.leader:
            self.leader = self.cluster.elect()

    def publish(self, topic, event):
        self.elect_leader()

        if not self.leader:
            print("[BROKER] No leader")
            return

        index = self.log.append({
            "topic": topic,
            "event": event,
            "leader": self.leader
        })

        self.topics[topic].append(index)
        print(f"[BROKER] leader={self.leader} idx={index}")

    async def start(self):
        while True:
            for topic, idxs in self.topics.items():
                while idxs:
                    i = idxs.pop(0)
                    entry = self.log.entries[i]

                    for handlers in self.subscribers.values():
                        for h in handlers:
                            await h(entry["event"])

            await asyncio.sleep(0.1)
