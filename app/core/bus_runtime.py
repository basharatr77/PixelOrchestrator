import asyncio

from app.agents.orchestrator.lifecycle_consumer import LifecycleConsumer
from app.agents.orchestrator.task_queue import TaskQueue
from app.core.event_bus import StreamBus
from app.core.registry import update_registry
from app.core.worker_pool import WorkerPool


class BusRuntime:
    def __init__(self):
        self.bus = StreamBus()
        self.pool = WorkerPool(self.bus, worker_count=3)
        self.task_queue = TaskQueue()

        self.lifecycle_consumer = LifecycleConsumer(
            task_queue=self.task_queue,
            registry_updater=update_registry,
        )

    def setup(self):
        self.lifecycle_consumer.subscribe(self.bus)

    async def run(self):
        self.setup()

        await self.pool.start()

        while True:
            await asyncio.sleep(3600)
