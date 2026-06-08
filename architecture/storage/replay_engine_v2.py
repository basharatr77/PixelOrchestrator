import json

class ReplayEngineV2:
    def __init__(self, commit_log):
        self.log = commit_log

    def replay(self, handler, topic=None, from_offset=0):
        events = self.log.load()

        for record in events:
            event = record["event"]
            offset = event.get("_offset", -1)

            # skip old events
            if offset < from_offset:
                continue

            if topic and record["topic"] != topic:
                continue

            handler(event)
