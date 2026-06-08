import asyncio
from collections import defaultdict, deque

class AsyncEventBroker:
    def __init__(self):
        self.topics = defaultdict(deque)
        self.subscribers = defaultdict(list)

    # PRODUCE
    async def publish(self, topic, event):
        self.topics[topic].append(event)
        print(f"[ASYNC BROKER] Published → {topic}")

    # CONSUME HANDLER REGISTRATION
    def subscribe(self, topic, handler):
        self.subscribers[topic].append(handler)
        print(f"[ASYNC BROKER] Subscribed → {topic}")

    # DISPATCH LOOP
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
