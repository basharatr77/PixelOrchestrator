from app.core.event_log import EventLog


class EventReplayer:
    def __init__(self):
        self.log = EventLog()

    def replay(self, from_offset=0, limit=100):
        events = self.log.read_from(from_offset, limit)
        print(f"🔁 Replaying {len(events)} events")
        return events
