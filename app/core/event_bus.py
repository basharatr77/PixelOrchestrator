import asyncio
from collections import defaultdict

from app.core.event_log import EventLog
from app.core.consumer_store import ConsumerStore


class StreamBus:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.handlers = defaultdict(list)
        self.log = EventLog()
        self.consumer_store = ConsumerStore()
        self.running = False

    def subscribe(self, group_id, event_type, handler):
        self.handlers[(group_id, event_type)].append(handler)

    async def publish(self, event):
        offset = self.log.append(event)
        await self.queue.put((offset, event))

    async def dispatch(self, offset, event):

        for (group_id, etype), handlers in self.handlers.items():

            if etype != event.type:
                continue

            last_offset = self.consumer_store.get_offset(
                group_id, etype
            )

            if offset <= last_offset:
                continue

            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event, offset, group_id)
                    else:
                        handler(event, offset, group_id)

                    self.consumer_store.commit(
                        group_id, etype, offset
                    )

                except Exception as e:
                    print("Handler error:", e)
