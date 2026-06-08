import json
import os

class IdempotencyStore:
    def __init__(self, file="idempotency.json"):
        self.file = file
        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                json.dump({}, f)

    def _load(self):
        with open(self.file, "r") as f:
            return json.load(f)

    def _save(self, data):
        with open(self.file, "w") as f:
            json.dump(data, f)

    def seen(self, consumer_id, event_id):
        data = self._load()
        return data.get(consumer_id, {}).get(event_id, False)

    def mark(self, consumer_id, event_id):
        data = self._load()

        if consumer_id not in data:
            data[consumer_id] = {}

        data[consumer_id][event_id] = True

        self._save(data)
