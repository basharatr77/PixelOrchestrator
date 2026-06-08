import json
import os
from datetime import datetime

class EventLogV2:
    def __init__(self, file="event_log.jsonl"):
        self.file = file
        if not os.path.exists(self.file):
            open(self.file, "w").close()

    def append(self, event):
        event["timestamp"] = str(datetime.utcnow())

        with open(self.file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def load_all(self):
        events = []
        with open(self.file, "r") as f:
            for i, line in enumerate(f):
                if line.strip():
                    e = json.loads(line)
                    e["_offset"] = i
                    events.append(e)
        return events
