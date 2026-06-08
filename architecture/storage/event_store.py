import json
from datetime import datetime

class EventStore:
    def __init__(self, file="events.jsonl"):
        self.file = file

    def save(self, event):
        event["timestamp"] = str(datetime.utcnow())
        with open(self.file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def load_all(self):
        with open(self.file, "r") as f:
            return [json.loads(line) for line in f]
