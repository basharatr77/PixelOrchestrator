from collections import defaultdict

class LagTrackerV2:
    def __init__(self):
        self.latest = defaultdict(int)
        self.committed = defaultdict(lambda: defaultdict(int))

    def update(self, topic, offset):
        self.latest[topic] = offset

    def commit(self, consumer, topic, offset):
        self.committed[consumer][topic] = offset

    def lag(self, consumer, topic):
        return self.latest[topic] - self.committed[consumer][topic]
