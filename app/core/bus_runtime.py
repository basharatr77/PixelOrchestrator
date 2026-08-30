import asyncio

from app.agents.device_agent.detector import run_detector_cycle
from app.agents.orchestrator.lifecycle_consumer import LifecycleConsumer
from app.agents.orchestrator.task_queue import TaskQueue
from app.agents.orchestrator.task_executor import TaskExecutor
from app.agents.orchestrator.execution_worker import ExecutionWorker
from app.core.event_bus import StreamBus
from app.core.device_registry import DeviceRegistry
from app.core.events import Event
from app.core.registry import create_registry_table, update_registry
from app.core.worker_pool import WorkerPool


class BusRuntime:
    def __init__(self, task_executor=None):
        create_registry_table()

        self.bus = StreamBus()
        self.pool = WorkerPool(self.bus, worker_count=3)
        self.task_queue = TaskQueue()
        self.device_registry = DeviceRegistry()

        self.task_executor = task_executor if task_executor is not None else TaskExecutor()

        self.execution_worker = ExecutionWorker(
            task_queue=self.task_queue,
            executor=self.task_executor,
        )

        self.execution_task = None
        self.detector_task = None
        self.known_devices = {}

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

    async def execution_loop(self):
        while True:
            if self.task_queue.tasks:
                self.execute_once()

            await asyncio.sleep(0.01)

    async def detector_loop_once(self):
        self.known_devices = await run_detector_cycle(
            self.bus,
            self.known_devices,
        )

        return self.known_devices

    async def detector_loop(self):
        while True:
            await self.detector_loop_once()
            await asyncio.sleep(3)

    async def run(self):
        self.setup()

        await self.pool.start()

        self.execution_task = asyncio.create_task(
            self.execution_loop()
        )

        self.detector_task = asyncio.create_task(
            self.detector_loop()
        )

        try:
            while True:
                await asyncio.sleep(3600)

        finally:
            tasks = []

            if self.execution_task is not None:
                self.execution_task.cancel()
                tasks.append(self.execution_task)

            if self.detector_task is not None:
                self.detector_task.cancel()
                tasks.append(self.detector_task)

            if tasks:
                await asyncio.gather(
                    *tasks,
                    return_exceptions=True,
                )

            await self.pool.stop()
