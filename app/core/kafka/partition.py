import os
import json

class Partition:
    def __init__(self, topic, pid):
        self.topic = topic
        self.pid = pid
        self.path = f"data/{topic}-p{pid}.log"
        os.makedirs("data", exist_ok=True)

        if not os.path.exists(self.path):
            open(self.path, "w").close()

    def append(self, event):
        record = {
            "type": event.type,
            "payload": event.payload,
            "ts": event.ts,
            "id": event.id
        }

        with open(self.path, "a") as f:
            offset = f.tell()
            f.write(json.dumps(record) + "\n")
            return offset

    def read(self, offset=0, limit=100):
        with open(self.path, "r") as f:
            f.seek(offset)
            out = []

            for _ in range(limit):
                line = f.readline()
                if not line:
                    break
                out.append(json.loads(line))
            return out
