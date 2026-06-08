class EventMetrics:
    def __init__(self):
        self.count = 0

    def record(self):
        self.count += 1

    def dump(self):
        return {"events_processed": self.count}
