import asyncio

from app.agents.device_agent import detector
from app.agents.device_agent.device_model import Device
from app.agents.orchestrator.lifecycle_consumer import LifecycleConsumer
from app.agents.orchestrator.task_queue import TaskQueue
from app.core.event_bus import StreamBus


def test_device_agent_to_orchestrator_end_to_end(monkeypatch):
    monkeypatch.setattr(
        detector,
        "scan_devices",
        lambda: [
            Device(serial="PIXEL_8", mode="ADB")
        ],
    )

    async def run():
        bus = StreamBus()
        queue = TaskQueue()
        registry = {}

        def update_registry(device, status, offset):
            registry[device] = status
            return True

        consumer = LifecycleConsumer(
            task_queue=queue,
            registry_updater=update_registry,
        )

        consumer.subscribe(bus)

        known = {}

        new_known = await detector.run_detector_cycle(
            bus,
            known,
        )

        assert new_known == {
            "PIXEL_8": "ADB",
        }

        assert bus.queue.qsize() == 1

        offset, event = await bus.queue.get()

        await bus.dispatch(
            offset,
            event,
        )

        assert event.type == "DEVICE_CONNECTED"

        assert registry == {
            "PIXEL_8": "ADB",
        }

        assert queue.tasks == [
            {
                "action": "safe_probe",
                "serial": "PIXEL_8",
            }
        ]

    asyncio.run(run())
