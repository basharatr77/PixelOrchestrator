import json
import os
from datetime import datetime

class EventLog:
    def __init__(self, file="event_log.jsonl"):
        self.file = file

        # create file if not exists
        if not os.path.exists(self.file):
            open(self.file, "w").close()

    def append(self, event):
        event["timestamp"] = str(datetime.utcnow())

        with open(self.file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def load_all(self):
        events = []
        with open(self.file, "r") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return events
