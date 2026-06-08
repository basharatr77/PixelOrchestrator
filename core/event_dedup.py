import time

class EventDeduplicator:
    def __init__(self, ttl=5):
        self.ttl = ttl
        self.cache = {}

    def is_duplicate(self, event_type, data):
        key = f"{event_type}:{data}"

        now = time.time()

        # cleanup old
        self.cache = {k:v for k,v in self.cache.items() if now - v < self.ttl}

        if key in self.cache:
            return True

        self.cache[key] = now
        return False
