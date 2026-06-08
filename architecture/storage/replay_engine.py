import json

class ReplayEngine:
    def __init__(self, commit_log):
        self.log = commit_log

    def replay(self, handler, topic=None):
        events = self.log.load()

        for record in events:
            if topic and record["topic"] != topic:
                continue

            event = record["event"]
            handler(event)
