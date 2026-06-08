import json
from datetime import datetime

class ReplayEngine:
    def __init__(self, store):
        self.store = store

    def replay_all(self, handler):
        events = self.store.load_all()

        for event in events:
            handler(event)

    def replay_from(self, timestamp, handler):
        events = self.store.load_all()

        for event in events:
            event_time = datetime.strptime(
                event["timestamp"],
                "%Y-%m-%d %H:%M:%S.%f"
            )

            if event_time >= timestamp:
                handler(event)

    def replay_device(self, device_id, handler):
        events = self.store.load_all()

        for event in events:
            if event["data"].get("id") == device_id:
                handler(event)
