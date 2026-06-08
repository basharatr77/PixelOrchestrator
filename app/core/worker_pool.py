import asyncio


class WorkerPool:
    """
    Parallel consumer worker pool (Kafka-style)
    """

    def __init__(self, bus, worker_count=3):
        self.bus = bus
        self.worker_count = worker_count
        self.tasks = []

    async def start(self):
        print(f"🚀 Starting {self.worker_count} workers")

        for i in range(self.worker_count):
            task = asyncio.create_task(self.worker(i))
            self.tasks.append(task)

    async def worker(self, wid):
        while True:
            offset, event = await self.bus.queue.get()

            print(f"[Worker-{wid}] Processing {event.type}")

            await self.bus.dispatch(offset, event)

    async def stop(self):
        for t in self.tasks:
            t.cancel()
