import asyncio
from collections import deque
import random

class AutoScalingWorkers:
    def __init__(self, min_w=2, max_w=8):
        self.min_w = min_w
        self.max_w = max_w
        self.current = min_w
        self.queue = deque()

    def submit(self, event):
        self.queue.append(event)

    def scale(self):
        load = len(self.queue)

        if load > 10 and self.current < self.max_w:
            self.current += 1
            print("[SCALE UP]", self.current)

        elif load < 3 and self.current > self.min_w:
            self.current -= 1
            print("[SCALE DOWN]", self.current)

    async def run(self):
        while True:
            self.scale()

            if self.queue:
                event = self.queue.popleft()
                print("[WORKER]", event)

            await asyncio.sleep(0.1)
