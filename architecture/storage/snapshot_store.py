import json, os

class SnapshotStore:
    def __init__(self, file="snapshot.json"):
        self.file = file

    def save(self, state):
        with open(self.file, "w") as f:
            json.dump(state, f)

    def load(self):
        if not os.path.exists(self.file):
            return None
        with open(self.file, "r") as f:
            return json.load(f)
