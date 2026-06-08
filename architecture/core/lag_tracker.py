from collections import defaultdict

class LagTracker:
    def __init__(self):
        self.consumer_offset = defaultdict(lambda: -1)
        self.latest_offset = defaultdict(lambda: -1)

    def update_latest(self, topic, offset):
        self.latest_offset[topic] = offset

    def commit(self, consumer_id, topic, offset):
        self.consumer_offset[(consumer_id, topic)] = offset

    def lag(self, consumer_id, topic):
        return self.latest_offset[topic] - self.consumer_offset[(consumer_id, topic)]
