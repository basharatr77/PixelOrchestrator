class EventBus:
    def __init__(self):
        self.subscribers = {}

    def publish(self, event_type, data):
        if event_type not in self.subscribers:
            return
        for cb in self.subscribers[event_type]:
            cb(data)

    def subscribe(self, event_type, callback):
        self.subscribers.setdefault(event_type, []).append(callback)

    def health(self):
        return {
            "event_types": len(self.subscribers),
            "status": "healthy"
        }
