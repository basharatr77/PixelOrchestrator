import asyncio
from collections import defaultdict
from architecture.core.raft_log import RaftLog
from architecture.core.raft_cluster_v2 import RaftClusterV2

class ReplicatedBrokerV4:
    def __init__(self, nodes):
        self.cluster = RaftClusterV2(nodes)
        self.log = RaftLog()

        # topic -> log indexes
        self.topics = defaultdict(list)

        # consumer groups
        self.subscribers = defaultdict(list)

        # simulated replication buffer
        self.replication_buffer = defaultdict(list)

        self.leader = None

    def subscribe(self, group_id, handler):
        self.subscribers[group_id].append(handler)

    def elect(self):
        if not self.leader:
            self.leader = self.cluster.elect()

    def publish(self, topic, event):
        self.elect()

        if not self.leader:
            print("[BROKER] no leader")
            return

        index = self.log.append({
            "topic": topic,
            "event": event,
            "leader": self.leader
        })

        # simulate replication
        self.replication_buffer[topic].append(index)

        self.topics[topic].append(index)

        print(f"[BROKER] leader={self.leader} index={index}")

    async def start(self):
        while True:
            # simulate replication delay
            for topic, buffer in self.replication_buffer.items():
                while buffer:
                    buffer.pop(0)

            # process committed entries
            for topic, idxs in self.topics.items():
                while idxs:
                    i = idxs.pop(0)
                    entry = self.log.entries[i]

                    for subs in self.subscribers.values():
                        for h in subs:
                            await h(entry["event"])

            await asyncio.sleep(0.1)
