import time

class RaftNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.term = 0
        self.last_heartbeat = time.time()

    def heartbeat(self):
        self.last_heartbeat = time.time()

    def is_alive(self, timeout=5):
        return (time.time() - self.last_heartbeat) < timeout
