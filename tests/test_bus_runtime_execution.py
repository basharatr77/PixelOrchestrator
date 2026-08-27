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


def test_bus_runtime_executes_lifecycle_task():
    runtime = make_runtime()

    runtime.setup()

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

    assert runtime.task_queue.tasks == []
