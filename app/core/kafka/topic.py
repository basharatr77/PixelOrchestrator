import hashlib
from app.core.kafka.partition import Partition

class Topic:
    def __init__(self, name, partitions=3):
        self.name = name
        self.partitions = [
            Partition(name, i) for i in range(partitions)
        ]
        self.n = partitions

    def route(self, key):
        h = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return h % self.n

    def publish(self, key, event):
        pid = self.route(key)
        offset = self.partitions[pid].append(event)
        return pid, offset
