import json
import os

class CommitLog:
    def __init__(self, file="commit_log.jsonl"):
        self.file = file
        if not os.path.exists(self.file):
            open(self.file, "w").close()

    def append(self, record):
        with open(self.file, "a") as f:
            f.write(json.dumps(record) + "\n")

    def load(self):
        with open(self.file, "r") as f:
            return [json.loads(x) for x in f if x.strip()]
