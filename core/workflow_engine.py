import asyncio

class WorkflowEngine:

    def __init__(self, bus, queue):
        self.bus = bus
        self.queue = queue

    async def start_workflow(self, device_id, steps):

        print(f"[WORKFLOW] Starting workflow for {device_id}")

        for step in steps:

            task_name = f"{step}_{device_id}"

            await self.queue.add_task(task_name)

            print(f"[TASK] Queued {task_name}")

            await asyncio.sleep(0.1)
