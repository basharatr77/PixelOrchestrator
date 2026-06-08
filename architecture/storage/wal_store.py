import json, os, time

class WALStore:
    def __init__(self, file="wal.log"):
        self.file = file
        if not os.path.exists(self.file):
            open(self.file, "w").close()

    def append(self, event):
        event["_ts"] = time.time()
        with open(self.file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def load(self):
        with open(self.file, "r") as f:
            return [json.loads(x) for x in f if x.strip()]
