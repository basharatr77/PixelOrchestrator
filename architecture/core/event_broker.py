import threading
import time
from collections import defaultdict, deque

class EventBroker:
    def __init__(self):
        # topic -> queue
        self.topics = defaultdict(deque)
        
        # topic -> subscribers
        self.subscribers = defaultdict(list)

        # lock for thread safety
        self.lock = threading.Lock()

    # ---------------------------
    # PRODUCER SIDE
    # ---------------------------
    def publish(self, topic, event):
        with self.lock:
            self.topics[topic].append(event)

        print(f"[BROKER] Event published to {topic}")

    # ---------------------------
    # CONSUMER SIDE
    # ---------------------------
    def subscribe(self, topic, handler):
        self.subscribers[topic].append(handler)
        print(f"[BROKER] Subscriber added to {topic}")

    # ---------------------------
    # DISPATCH LOOP
    # ---------------------------
    def start(self, poll_interval=0.5):
        def run():
            while True:
                with self.lock:
                    for topic, queue in self.topics.items():
                        if queue and topic in self.subscribers:
                            event = queue.popleft()

                            for handler in self.subscribers[topic]:
                                try:
                                    handler(event)
                                except Exception as e:
                                    print("[BROKER ERROR]", e)

                time.sleep(poll_interval)

        t = threading.Thread(target=run, daemon=True)
        t.start()
