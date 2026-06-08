import asyncio
from collections import deque

class WorkerPool:
    def __init__(self, workers=2):
        self.workers = workers
        self.queue = deque()

    def scale(self, n):
        print(f"[WORKERS] Scaling {self.workers} → {n}")
        self.workers = n

    def submit(self, event):
        self.queue.append(event)

    async def run(self):
        while True:
            if self.queue:
                event = self.queue.popleft()
                print("[WORKER]", event)
            await asyncio.sleep(0.05)
