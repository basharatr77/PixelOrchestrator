import asyncio

from app.core.module_contract import Device, DeviceState, ModuleType
from app.agents.device_agent import detector
from app.core.event_bus import StreamBus
from app.core.events import Event


def test_device_connected_lifecycle_publishes_event(monkeypatch):
    monkeypatch.setattr(
        detector,
        "scan_devices",
        lambda: [
            Device(
                device_id="adb:PIXEL_8",
                module_type=ModuleType.ADB,
                state=DeviceState.ADB,
                serial="PIXEL_8",
                transport="adb",
            )
        ],
    )

    async def run():
        bus = StreamBus()

        lifecycle_events = detector.detect_lifecycle({})

        assert len(lifecycle_events) == 1

        lifecycle = lifecycle_events[0]

        event = Event(
            lifecycle["type"],
            lifecycle["data"],
        )

        await bus.publish(event)

        assert bus.queue.qsize() == 1

        offset, queued_event = await bus.queue.get()

        assert queued_event.type == "DEVICE_CONNECTED"
        assert queued_event.payload == {
            "serial": "PIXEL_8",
            "mode": "ADB",
            "brand": "",
            "model": "",
            "android_version": "",
        }

    asyncio.run(run())
