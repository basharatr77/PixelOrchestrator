import asyncio

from app.core.bus_runtime import BusRuntime
from app.core.events import Event


def test_bus_runtime_automatically_executes_lifecycle_task():
    async def run():
        runtime = BusRuntime()

        registry = {}

        def update_registry(device, status):
            registry[device] = status

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

        await runtime.pool.start()

        runtime.execution_task = asyncio.create_task(
            runtime.execution_loop()
        )

        for _ in range(100):
            if (
                registry.get("PIXEL_8") == "ADB"
                and not runtime.task_queue.tasks
            ):
                break

            await asyncio.sleep(0.01)

        assert registry == {
            "PIXEL_8": "ADB",
        }

        assert runtime.task_queue.tasks == []

        events = runtime.bus.log.read_from(
            offset=0,
            limit=100,
        )

        task_events = [
            event
            for event in events
            if event["type"] == "TASK_EXECUTED"
            and event["payload"].get("serial") == "PIXEL_8"
        ]

        assert task_events

        assert task_events[-1]["payload"] == {
            "success": True,
            "action": "safe_probe",
            "serial": "PIXEL_8",
        }

        runtime.execution_task.cancel()
        await runtime.pool.stop()

    asyncio.run(run())
