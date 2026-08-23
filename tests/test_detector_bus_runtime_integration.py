import asyncio

from app.agents.device_agent import detector
from app.agents.device_agent.device_model import Device
from app.core.bus_runtime import BusRuntime


def test_detector_to_bus_runtime_executes_lifecycle_task(monkeypatch):
    async def run():
        runtime = BusRuntime()

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
                offset=0,
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

        assert task_events

        assert task_events[-1]["payload"] == {
            "success": True,
            "action": "safe_probe",
            "serial": "PIXEL_8",
        }

        assert runtime.task_queue.tasks == []

        runtime.execution_task.cancel()
        await asyncio.gather(
            runtime.execution_task,
            return_exceptions=True,
        )

        await runtime.pool.stop()

    asyncio.run(run())
