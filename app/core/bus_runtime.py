import asyncio

from app.agents.device_agent.detector import run_detector_cycle
from app.agents.orchestrator.lifecycle_consumer import LifecycleConsumer
from app.agents.orchestrator.task_queue import TaskQueue
from app.agents.orchestrator.task_executor import TaskExecutor
from app.agents.orchestrator.execution_worker import ExecutionWorker
from app.core.event_bus import StreamBus
from app.core.device_registry import DeviceRegistry
from app.core.events import Event
from app.core.registry import create_registry_table, update_registry, read_registry
from app.core.worker_pool import WorkerPool


class BusRuntime:
    def __init__(self, task_executor=None):
        create_registry_table()

        self.bus = StreamBus()
        self.pool = WorkerPool(self.bus, worker_count=3)
        self.task_queue = TaskQueue()
        self.device_registry = DeviceRegistry()

        self._rehydrate_registry()

        self.task_executor = (
            task_executor
            if task_executor is not None
            else TaskExecutor(
                progress_callback=self._publish_task_progress,
            )
        )

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
            device_registry=self.device_registry,
        )

    @staticmethod
    def _rehydration_contract(status):
        from app.core.module_contract import DeviceState, ModuleType

        mapping = {
            "ADB": (DeviceState.ADB, ModuleType.ADB),
            "FASTBOOT": (DeviceState.FASTBOOT, ModuleType.FASTBOOT),
            "FASTBOOTD": (DeviceState.FASTBOOTD, ModuleType.FASTBOOT),
            "RECOVERY": (DeviceState.RECOVERY, ModuleType.COMMON),
            "SIDELOAD": (DeviceState.SIDELOAD, ModuleType.COMMON),
            "EDL": (DeviceState.EDL, ModuleType.QUALCOMM),
            "BROM": (DeviceState.BROM, ModuleType.MEDIATEK),
            "PRELOADER": (DeviceState.PRELOADER, ModuleType.MEDIATEK),
            "DOWNLOAD": (DeviceState.DOWNLOAD, ModuleType.SAMSUNG),
            "disconnected": (
                DeviceState.DISCONNECTED,
                ModuleType.COMMON,
            ),
        }

        if status not in mapping:
            raise ValueError(
                f"Unsupported persisted device status: {status!r}"
            )

        return mapping[status]

    def _rehydrate_registry(self):
        from app.core.module_contract import Device

        for serial, status, _offset in read_registry():
            state, module_type = self._rehydration_contract(status)

            device = Device(
                device_id=f"device:{serial}",
                module_type=module_type,
                state=state,
                model=None,
                serial=serial,
                transport=None,
                properties={},
            )

            self.device_registry.register(device)

    def setup(self):
        self.lifecycle_consumer.subscribe(self.bus)

    def _publish_task_progress(self, task, progress, message=""):
        self.bus.publish_now(
            Event(
                type="TASK_PROGRESS",
                payload={
                    "task_id": task.id,
                    "progress": progress,
                    "message": message,
                },
            )
        )

    @staticmethod
    def _serialize_task_result(result):
        from dataclasses import asdict, is_dataclass

        if is_dataclass(result):
            return asdict(result)

        return result

    def execute_once(self, task=None):
        if task is not None:
            self.task_queue.add_task(task)

        result = self.execution_worker.run_once()

        if result is not None:
            self.bus.publish_now(
                Event(
                    type="TASK_EXECUTED",
                    payload=self._serialize_task_result(result),
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
