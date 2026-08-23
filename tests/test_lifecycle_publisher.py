import asyncio

from app.agents.device_agent import detector
from app.agents.device_agent.device_model import Device
from app.core.event_bus import StreamBus


def test_lifecycle_events_are_published_to_eventbus(monkeypatch):
    monkeypatch.setattr(
        detector,
        "scan_devices",
        lambda: [
            Device(serial="PIXEL_8", mode="ADB")
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
