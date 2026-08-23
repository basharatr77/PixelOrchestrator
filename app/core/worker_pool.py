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
        if self.tasks:
            return

        print(f"🚀 Starting {self.worker_count} workers")

        for i in range(self.worker_count):
            task = asyncio.create_task(self.worker(i))
            self.tasks.append(task)

    async def worker(self, wid):
        while True:
            offset, event = await self.bus.queue.get()

            try:
                print(f"[Worker-{wid}] Processing {event.type}")

                try:
                    await self.bus.dispatch(offset, event)
                except Exception as e:
                    print(f"[Worker-{wid}] Dispatch error:", e)

            finally:
                self.bus.queue.task_done()

    async def stop(self):
        if not self.tasks:
            return

        for task in self.tasks:
            task.cancel()

        await asyncio.gather(
            *self.tasks,
            return_exceptions=True,
        )

        self.tasks.clear()
