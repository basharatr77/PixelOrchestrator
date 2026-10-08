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
        self._dispatch_locks = {}
        self._failed_offsets = {}

    def subscribe(self, group_id, event_type, handler):
        self.handlers[(group_id, event_type)].append(handler)

    async def publish(self, event):
        offset = self.log.append(event)
        await self.queue.put((offset, event))
        return offset

    def publish_now(self, event):
        offset = self.log.append(event)
        self.queue.put_nowait((offset, event))
        return offset

    async def dispatch(self, offset, event):
        for (group_id, etype), handlers in self.handlers.items():

            if etype != event.type:
                continue

            key = (group_id, etype)
            lock = self._dispatch_locks.setdefault(key, asyncio.Lock())

            async with lock:
                last_offset = self.consumer_store.get_offset(
                    group_id, etype
                )

                if offset <= last_offset:
                    continue

                failed_offset = self._failed_offsets.get(key)
                if failed_offset is not None and offset > failed_offset:
                    continue

                try:
                    for handler in handlers:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event, offset, group_id)
                        else:
                            handler(event, offset, group_id)

                    self.consumer_store.commit(
                        group_id, etype, offset
                    )
                    if self._failed_offsets.get(key) == offset:
                        del self._failed_offsets[key]

                except asyncio.CancelledError:
                    self._failed_offsets[key] = min(
                        offset,
                        self._failed_offsets.get(key, offset),
                    )
                    raise

                except Exception as e:
                    self._failed_offsets[key] = min(
                        offset,
                        self._failed_offsets.get(key, offset),
                    )
                    print("Handler error:", e)
