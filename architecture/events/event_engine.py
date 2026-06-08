class EventEngine:
    def __init__(self):
        self.subscribers = {}
        self.event_log = []

    def subscribe(self, event_type, handler):
        self.subscribers.setdefault(event_type, []).append(handler)

    def emit(self, event_type, data):
        event = {"type": event_type, "data": data}
        self.event_log.append(event)

        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                handler(data)
