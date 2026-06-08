import json
import os

class OffsetStore:
    def __init__(self, file="offsets.json"):
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

    def get(self, consumer_id, topic):
        data = self._load()
        return data.get(consumer_id, {}).get(topic, -1)

    def commit(self, consumer_id, topic, offset):
        data = self._load()

        if consumer_id not in data:
            data[consumer_id] = {}

        data[consumer_id][topic] = offset
        self._save(data)
