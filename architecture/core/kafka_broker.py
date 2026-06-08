import asyncio
from collections import defaultdict, deque
from architecture.storage.event_log_v2 import EventLogV2
from architecture.storage.offset_store import OffsetStore

class KafkaStyleBroker:
    def __init__(self):
        self.topics = defaultdict(deque)
        self.subscribers = defaultdict(list)

        self.log = EventLogV2()
        self.offsets = OffsetStore()

    async def publish(self, topic, event):
        # ensure event has safe structure
        event = dict(event)

        # assign offset BEFORE storing (IMPORTANT FIX)
        current_offset = len(self.log.load_all())

        event["_offset"] = current_offset

        self.log.append(event)
        self.topics[topic].append(event)

        print(f"[KAFKA] Published → {topic}")

    def subscribe(self, consumer_id, topic, handler):
        self.subscribers[topic].append((consumer_id, handler))
        print(f"[KAFKA] Consumer {consumer_id} subscribed → {topic}")

    async def start(self, delay=0.1):
        while True:
            for topic, queue in self.topics.items():

                if not queue:
                    continue

                for consumer_id, handler in self.subscribers[topic]:

                    last_offset = self.offsets.get(consumer_id, topic)

                    for event in list(queue):

                        event_offset = event.get("_offset", -1)

                        # SAFE CHECK (FIXED)
                        if event_offset <= last_offset:
                            continue

                        try:
                            await handler(event)

                            self.offsets.update(
                                consumer_id,
                                topic,
                                event_offset
                            )

                        except Exception as e:
                            print("[KAFKA ERROR]", e)

            await asyncio.sleep(delay)
