import asyncio
from collections import defaultdict, deque
from architecture.storage.event_log_v2 import EventLogV2
from architecture.storage.offset_store import OffsetStore
from architecture.storage.dead_letter import DeadLetterQueue
from architecture.schema.event_schema import EventSchema

class KafkaStyleBrokerV2:
    def __init__(self):
        self.topics = defaultdict(deque)
        self.subscribers = defaultdict(list)

        self.log = EventLogV2()
        self.offsets = OffsetStore()
        self.dlq = DeadLetterQueue()

    async def publish(self, topic, event):
        ok, msg = EventSchema.validate(event)
        if not ok:
            self.dlq.push(event, msg)
            print("[KAFKA] REJECTED EVENT → DLQ")
            return

        self.log.append(event)
        self.topics[topic].append(event)

        print(f"[KAFKA V2] Published → {topic}")

    def subscribe(self, consumer_id, topic, handler):
        self.subscribers[topic].append((consumer_id, handler))
        print(f"[KAFKA V2] {consumer_id} subscribed → {topic}")

    async def start(self, delay=0.1):
        while True:
            for topic, queue in self.topics.items():
                if not queue:
                    continue

                for consumer_id, handler in self.subscribers[topic]:
                    last_offset = self.offsets.get(consumer_id, topic)

                    for event in list(queue):
                        offset = event.get("_offset", -1)
                        if offset <= last_offset:
                            continue

                        try:
                            await handler(event)

                            self.offsets.update(
                                consumer_id,
                                topic,
                                offset
                            )

                        except Exception as e:
                            self.dlq.push(event, e)
                            print("[KAFKA V2 ERROR]", e)

            await asyncio.sleep(delay)
