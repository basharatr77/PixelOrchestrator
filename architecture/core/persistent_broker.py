import asyncio
from collections import defaultdict, deque
from architecture.storage.event_log import EventLog

class PersistentEventBroker:
    def __init__(self):
        self.topics = defaultdict(deque)
        self.subscribers = defaultdict(list)
        self.log = EventLog()

    async def publish(self, topic, event):
        # 1. store to disk (CRITICAL)
        self.log.append(event)

        # 2. store in memory queue
        self.topics[topic].append(event)

        print(f"[PERSISTENT BROKER] Saved → {topic}")

    def subscribe(self, topic, handler):
        self.subscribers[topic].append(handler)
        print(f"[PERSISTENT BROKER] Subscribed → {topic}")

    async def start(self, delay=0.1):
        while True:
            for topic, queue in self.topics.items():
                if queue and topic in self.subscribers:
                    event = queue.popleft()

                    for handler in self.subscribers[topic]:
                        try:
                            await handler(event)
                        except Exception as e:
                            print("[BROKER ERROR]", e)

            await asyncio.sleep(delay)
