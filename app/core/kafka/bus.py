from app.core.kafka.topic import Topic
from app.core.kafka.consumer_store import ConsumerStore

class KafkaBus:
    def __init__(self):
        self.topic = Topic("events", partitions=3)
        self.store = ConsumerStore()
        self.handlers = {}

    def subscribe(self, group, handler):
        self.handlers[group] = handler

    async def publish(self, event):
        key = event.payload.get("id", "default")
        return self.topic.publish(key, event)

    async def dispatch(self, event, pid, offset):
        for group, handler in self.handlers.items():

            last = self.store.get(group, "events", pid)

            if offset <= last:
                continue

            await handler(event, pid, offset)

            self.store.commit(group, "events", pid, offset)
