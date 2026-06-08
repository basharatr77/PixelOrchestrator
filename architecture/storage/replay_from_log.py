from architecture.storage.event_log import EventLog

class ReplayFromLog:
    def __init__(self):
        self.log = EventLog()

    def replay_all(self, handler):
        events = self.log.load_all()

        for event in events:
            handler(event)
