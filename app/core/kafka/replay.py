class Replay:
    def __init__(self, topic):
        self.topic = topic

    def replay_all(self):
        data = []
        for p in self.topic.partitions:
            data.extend(p.read(0, 1000))
        return data
