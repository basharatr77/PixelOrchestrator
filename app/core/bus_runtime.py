import asyncio

from app.agents.orchestrator.lifecycle_consumer import LifecycleConsumer
from app.agents.orchestrator.task_queue import TaskQueue
from app.agents.orchestrator.task_executor import TaskExecutor
from app.agents.orchestrator.execution_worker import ExecutionWorker
from app.core.events import Event
from app.core.event_bus import StreamBus
from app.core.registry import update_registry
from app.core.worker_pool import WorkerPool


class BusRuntime:
    def __init__(self):
        self.bus = StreamBus()
        self.pool = WorkerPool(self.bus, worker_count=3)
        self.task_queue = TaskQueue()

        self.task_executor = TaskExecutor()

        self.execution_worker = ExecutionWorker(
            task_queue=self.task_queue,
            executor=self.task_executor,
        )

        self.lifecycle_consumer = LifecycleConsumer(
            task_queue=self.task_queue,
            registry_updater=update_registry,
        )

    def setup(self):
        self.lifecycle_consumer.subscribe(self.bus)

    def execute_once(self, task=None):
        if task is not None:
            self.task_queue.add_task(task)

        result = self.execution_worker.run_once()

        if result is not None:
            self.bus.publish_now(
                Event(
                    type="TASK_EXECUTED",
                    payload=result,
                )
            )

        return result

    async def run(self):
        self.setup()

        await self.pool.start()

        while True:
            await asyncio.sleep(3600)
