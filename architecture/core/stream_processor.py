import asyncio
from collections import defaultdict, deque

class StreamProcessor:
    def __init__(self, max_queue=100):
        self.topics = defaultdict(deque)
        self.handlers = defaultdict(list)
        self.max_queue = max_queue

    def publish(self, topic, event):
        queue = self.topics[topic]

        if len(queue) >= self.max_queue:
            print("[STREAM] Backpressure applied, dropping event")
            return

        queue.append(event)
        print(f"[STREAM] Event queued → {topic}")

    def subscribe(self, topic, handler):
        self.handlers[topic].append({
            "fn": handler,
            "retries": 3
        })

        print(f"[STREAM] Subscribed → {topic}")

    async def start(self, delay=0.05):
        while True:
            for topic, queue in self.topics.items():
                if not queue:
                    continue

                event = queue.popleft()

                for sub in self.handlers[topic]:
                    handler = sub["fn"]

                    try:
                        await handler(event)

                    except Exception as e:
                        sub["retries"] -= 1

                        if sub["retries"] > 0:
                            print("[STREAM] Retry event")
                            queue.append(event)
                        else:
                            print("[STREAM] Event dropped permanently")

            await asyncio.sleep(delay)
