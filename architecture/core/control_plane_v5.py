import time
from collections import defaultdict

class ControlPlaneV5:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.last_seen = {}

    def heartbeat(self, consumer_id):
        self.last_seen[consumer_id] = time.time()

    def alive(self, consumer_id):
        return (time.time() - self.last_seen.get(consumer_id, 0)) < self.timeout

    def active(self):
        return [
            cid for cid in self.last_seen
            if self.alive(cid)
        ]
