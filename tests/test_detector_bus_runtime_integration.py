import asyncio

from app.agents.device_agent import detector
from app.agents.device_agent.device_model import Device
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
        assert device.mode == "ADB"

        return FakeTransport()


def make_runtime():
    return BusRuntime(
        task_executor=TaskExecutor(
            transport_resolver=FakeTransportResolver,
        )
    )


def test_detector_to_bus_runtime_executes_lifecycle_task(monkeypatch):
    async def run():
        runtime = make_runtime()

        registry = {}

        def update_registry(device, status):
            registry[device] = status

        runtime.lifecycle_consumer.registry_updater = update_registry

        monkeypatch.setattr(
            detector,
            "scan_devices",
            lambda: [
                Device(serial="PIXEL_8", mode="ADB")
            ],
        )

        runtime.setup()

        start_offset = runtime.bus.log.latest_offset()

        await runtime.pool.start()

        runtime.execution_task = asyncio.create_task(
            runtime.execution_loop()
        )

        known = {}

        new_known = await detector.run_detector_cycle(
            runtime.bus,
            known,
        )

        assert new_known == {
            "PIXEL_8": "ADB",
        }

        for _ in range(100):
            events = runtime.bus.log.read_from(
                offset=start_offset,
                limit=100,
            )

            task_events = [
                event
                for event in events
                if event["type"] == "TASK_EXECUTED"
                and event["payload"].get("serial") == "PIXEL_8"
            ]

            if registry.get("PIXEL_8") == "ADB" and task_events:
                break

            await asyncio.sleep(0.01)

        assert registry == {
            "PIXEL_8": "ADB",
        }

        assert runtime.task_queue.tasks == []

        assert task_events

        assert task_events[-1]["payload"] == {
            "success": True,
            "action": "safe_probe",
            "serial": "PIXEL_8",
            "returncode": 0,
            "stdout": "Pixel 8\n",
            "stderr": "",
        }

        runtime.execution_task.cancel()

        await asyncio.gather(
            runtime.execution_task,
            return_exceptions=True,
        )

        await runtime.pool.stop()

    asyncio.run(run())
