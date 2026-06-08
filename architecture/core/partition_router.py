import hashlib

class PartitionRouter:
    def __init__(self, partitions=3):
        self.partitions = partitions

    def route(self, key):
        h = hashlib.sha256(key.encode()).hexdigest()
        return int(h[:8], 16) % self.partitions
