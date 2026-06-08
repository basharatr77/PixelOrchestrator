import json
from datetime import datetime

class DeadLetterQueue:
    def __init__(self, file="dlq.jsonl"):
        self.file = file

    def push(self, event, error):
        payload = {
            "event": event,
            "error": str(error),
            "timestamp": str(datetime.utcnow())
        }

        with open(self.file, "a") as f:
            f.write(json.dumps(payload) + "\n")
