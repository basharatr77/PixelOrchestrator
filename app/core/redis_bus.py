import redis
import json
import threading

class RedisEventBus:
    def __init__(self, host="localhost", port=6379):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        self.handlers = {}
        self.queue_key = "event_queue"

    def subscribe(self, event_type, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    def publish(self, event):
        self.r.lpush(self.queue_key, json.dumps(event))

    def run(self):
        print("🚀 Redis EventBus running (scalable mode)")
        while True:
            _, data = self.r.brpop(self.queue_key)
            event = json.loads(data)

            etype = event.get("type")
            print("EVENT:", event)

            for h in self.handlers.get(etype, []):
                try:
                    h(event)
                except Exception as e:
                    print("Handler error:", e)
