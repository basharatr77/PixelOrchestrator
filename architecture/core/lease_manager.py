class LeaseManager:
    def __init__(self):
        self.leases = {}  # partition -> consumer

    def acquire(self, partition, consumer_id):
        self.leases[partition] = consumer_id

    def release_dead(self, active_consumers):
        self.leases = {
            p: c for p, c in self.leases.items()
            if c in active_consumers
        }

    def owner(self, partition):
        return self.leases.get(partition)
