import asyncio
from collections import deque

class AutoScalerV2:
    def __init__(self, min_w=2, max_w=10):
        self.min_w = min_w
        self.max_w = max_w
        self.current = min_w
        self.queue = deque()

    def submit(self, event):
        self.queue.append(event)

    def scale(self):
        load = len(self.queue)

        if load > 20 and self.current < self.max_w:
            self.current += 1
            print("[AUTO SCALE UP]", self.current)

        elif load < 5 and self.current > self.min_w:
            self.current -= 1
            print("[AUTO SCALE DOWN]", self.current)

    async def run(self):
        while True:
            self.scale()

            if self.queue:
                event = self.queue.popleft()
                print("[AUTO WORKER]", event)

            await asyncio.sleep(0.05)
