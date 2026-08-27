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
