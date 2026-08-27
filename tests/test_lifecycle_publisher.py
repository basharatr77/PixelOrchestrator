import asyncio

from app.agents.device_agent import detector
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.event_bus import StreamBus


def test_lifecycle_events_are_published_to_eventbus(monkeypatch):
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

        await detector.publish_lifecycle_events(
            bus,
            lifecycle_events,
        )

        queued_offset, queued_event = await bus.queue.get()

        assert queued_event.type == "DEVICE_CONNECTED"
        assert queued_event.payload == {
            "serial": "PIXEL_8",
            "mode": "ADB",
            "brand": "",
            "model": "",
            "android_version": "",
        }

    asyncio.run(run())
