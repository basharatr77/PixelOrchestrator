import asyncio

from app.agents.orchestrator.task_queue import TaskQueue
from app.core.bus_runtime import BusRuntime
from app.core.events import Event


def test_bus_runtime_dispatches_lifecycle_event(monkeypatch):
    async def run():
        runtime = BusRuntime()

        registry = {}

        def update_registry(device, status, offset):
            registry[device] = status
            return True

        runtime.lifecycle_consumer.registry_updater = update_registry

        runtime.setup()

        await runtime.bus.publish(
            Event(
                "DEVICE_CONNECTED",
                {
                    "serial": "PIXEL_8",
                    "mode": "ADB",
                    "brand": "",
                    "model": "",
                    "android_version": "",
                },
            )
        )

        assert runtime.bus.queue.qsize() == 1

        await runtime.pool.start()

        for _ in range(50):
            if runtime.task_queue.tasks:
                break
            await asyncio.sleep(0.01)

        assert registry == {
            "PIXEL_8": "ADB",
        }

        assert runtime.task_queue.tasks == [
            {
                "action": "safe_probe",
                "serial": "PIXEL_8",
            }
        ]

        await runtime.pool.stop()

    asyncio.run(run())
