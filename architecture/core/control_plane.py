import time
from collections import defaultdict

class ControlPlane:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.heartbeats = {}

    def beat(self, consumer_id):
        self.heartbeats[consumer_id] = time.time()

    def is_alive(self, consumer_id):
        last = self.heartbeats.get(consumer_id)
        if not last:
            return False
        return (time.time() - last) < self.timeout

    def get_active_consumers(self):
        return [
            cid for cid in self.heartbeats
            if self.is_alive(cid)
        ]
