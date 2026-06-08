import asyncio
from collections import defaultdict, deque
from architecture.core.control_plane import ControlPlane
from architecture.core.auto_rebalancer import AutoRebalancer

class ControlBroker:
    def __init__(self, partitions=3):
        self.partitions = partitions
        self.topics = defaultdict(lambda: [deque() for _ in range(partitions)])
        self.subscribers = defaultdict(list)

        self.cp = ControlPlane()
        self.rebalancer = AutoRebalancer(self, self.cp)
        self.assignment = {}

    def publish(self, topic, event):
        self.topics[topic][0].append(event)
        print(f"[CONTROL BROKER] Published → {topic}")

    def subscribe(self, group_id, consumer_id, handler):
        self.subscribers[group_id].append({
            "id": consumer_id,
            "handler": handler
        })

        self.cp.beat(consumer_id)
        self.rebalancer.rebalance(group_id)

    def heartbeat(self, consumer_id):
        self.cp.beat(consumer_id)

    async def start(self, delay=0.5):
        while True:
            for topic, partitions in self.topics.items():
                for queue in partitions:
                    if not queue:
                        continue

                    event = queue.popleft()

                    for group_id, consumers in self.subscribers.items():
                        for c in consumers:
                            cid = c["id"]

                            if not self.cp.is_alive(cid):
                                continue

                            try:
                                await c["handler"](event)
                            except Exception as e:
                                print("[CONTROL ERROR]", e)

            await asyncio.sleep(delay)
