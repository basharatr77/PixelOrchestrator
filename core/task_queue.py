import asyncio

class TaskQueue:

    def __init__(self):
        self.queue = asyncio.Queue()

    async def add_task(self, task):
        await self.queue.put(task)

    async def worker(self):

        while True:
            task = await self.queue.get()

            print(f"[TASK] Running {task}")
            await asyncio.sleep(1)
            print(f"[TASK] Finished {task}")
