import asyncio

from app.agents.orchestrator.task_executor import TaskExecutor
from app.core.bus_runtime import BusRuntime


class FakeTransport:
    def execute(self, command):
        assert command == "getprop ro.product.model"

        return {
            "returncode": 0,
            "stdout": "Pixel 8\n",
            "stderr": "",
        }


class FakeTransportResolver:
    @staticmethod
    def resolve(device):
        assert device.serial == "PIXEL_8"
        assert device.state.value.upper() == "ADB"

        return FakeTransport()


def make_runtime():
    return BusRuntime(
        task_executor=TaskExecutor(
            transport_resolver=FakeTransportResolver,
        )
    )


def test_bus_runtime_publishes_task_executed_event():
    async def run():
        runtime = make_runtime()

        result = runtime.execute_once({
            "action": "safe_probe",
            "serial": "PIXEL_8",
        })

        assert result == {
            "success": True,
            "action": "safe_probe",
            "serial": "PIXEL_8",
            "returncode": 0,
            "stdout": "Pixel 8\n",
            "stderr": "",
        }

        assert runtime.bus.queue.qsize() == 1

        offset, event = await runtime.bus.queue.get()

        assert event.type == "TASK_EXECUTED"
        assert event.payload == {
            "success": True,
            "action": "safe_probe",
            "serial": "PIXEL_8",
            "returncode": 0,
            "stdout": "Pixel 8\n",
            "stderr": "",
        }

    asyncio.run(run())

from app.core.module_contract import Action, ActionResult, ModuleManifest, ModuleType
from app.core.task import Task, TaskStatus


class FakeCanonicalModule:
    manifest = ModuleManifest(
        id="fake",
        name="Fake Module",
        version="1.0",
        module_type=ModuleType.COMMON,
        actions=(
            Action(
                id="probe",
                name="Probe",
                requires_device=False,
            ),
        ),
    )

    def get_actions(self):
        return self.manifest.actions

    def execute(self, action_id, device=None, **parameters):
        assert action_id == "probe"
        assert device is None
        assert parameters == {"source": "bus"}
        return ActionResult(
            success=True,
            message="canonical-bus-ok",
            data={"source": "bus"},
        )


class FakeCanonicalModuleRegistry:
    def get(self, module_id):
        assert module_id == "fake"
        return FakeCanonicalModule()


def test_bus_runtime_executes_canonical_task_and_publishes_event():
    runtime = BusRuntime(
        task_executor=TaskExecutor(
            module_registry=FakeCanonicalModuleRegistry(),
        )
    )

    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="probe",
        parameters={"source": "bus"},
    )

    result = runtime.execute_once(task)

    assert result.success is True
    assert result.message == "canonical-bus-ok"
    assert result.data == {"source": "bus"}
    assert task.status is TaskStatus.COMPLETED
    assert task.attempts == 1

    assert runtime.bus.queue.qsize() == 1

    offset, event = runtime.bus.queue.get_nowait()

    assert event.type == "TASK_EXECUTED"
    assert event.payload == {
        "success": True,
        "message": "canonical-bus-ok",
        "data": {"source": "bus"},
        "error_code": None,
    }

from app.core.module_contract import Action, ActionResult, ModuleManifest, ModuleType
from app.core.task import Task, TaskStatus


class FakeCanonicalModule:
    manifest = ModuleManifest(
        id="fake",
        name="Fake Module",
        version="1.0",
        module_type=ModuleType.COMMON,
        actions=(
            Action(
                id="probe",
                name="Probe",
                requires_device=False,
            ),
        ),
    )

    def get_actions(self):
        return self.manifest.actions

    def execute(self, action_id, device=None, **parameters):
        assert action_id == "probe"
        assert device is None
        assert parameters == {"source": "bus"}
        return ActionResult(
            success=True,
            message="canonical-bus-ok",
            data={"source": "bus"},
        )


class FakeCanonicalModuleRegistry:
    def get(self, module_id):
        assert module_id == "fake"
        return FakeCanonicalModule()


def test_bus_runtime_canonical_result_event_contract():
    runtime = BusRuntime(
        task_executor=TaskExecutor(
            module_registry=FakeCanonicalModuleRegistry(),
        )
    )

    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="probe",
        parameters={"source": "bus"},
    )

    result = runtime.execute_once(task)

    assert result.success is True
    assert task.status is TaskStatus.COMPLETED
    assert task.attempts == 1

    assert runtime.bus.queue.qsize() == 1

    offset, event = runtime.bus.queue.get_nowait()

    assert event.type == "TASK_EXECUTED"
    assert isinstance(event.payload, dict)
    assert event.payload == {
        "success": True,
        "message": "canonical-bus-ok",
        "data": {"source": "bus"},
        "error_code": None,
    }
