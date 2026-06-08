import asyncio
from asyncio import Queue

class ParallelWorkers:
    def __init__(self, workers=3, max_queue=50):
        self.queue = Queue(maxsize=max_queue)
        self.workers = workers

    async def submit(self, event):
        await self.queue.put(event)

    async def _worker(self, wid):
        while True:
            event = await self.queue.get()
            print(f"[WORKER-{wid}]", event)
            await asyncio.sleep(0.05)

    async def run(self):
        tasks = []
        for i in range(self.workers):
            tasks.append(asyncio.create_task(self._worker(i)))
        await asyncio.gather(*tasks)
