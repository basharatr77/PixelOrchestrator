import json
import os

class EventStoreV3:
    def __init__(self, file="event_log.jsonl"):
        self.file = file

    def append(self, event):
        with open(self.file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def load(self):
        if not os.path.exists(self.file):
            return []

        with open(self.file, "r") as f:
            return [json.loads(x) for x in f if x.strip()]
