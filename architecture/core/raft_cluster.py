import time
import random

class RaftCluster:
    def __init__(self, timeout=5):
        self.nodes = {}
        self.leader = None
        self.timeout = timeout
        self.term = 0

    def register(self, node_id):
        self.nodes[node_id] = time.time()

    def heartbeat(self, node_id):
        self.nodes[node_id] = time.time()

    def elect_leader(self):
        alive = [
            n for n, t in self.nodes.items()
            if time.time() - t < self.timeout
        ]

        if not alive:
            self.leader = None
            return None

        self.leader = random.choice(alive)
        self.term += 1
        return self.leader

    def get_leader(self):
        return self.leader
