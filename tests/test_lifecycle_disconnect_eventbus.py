import asyncio

from app.agents.device_agent import detector
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.event_bus import StreamBus


def test_device_disconnected_lifecycle_reaches_subscriber(monkeypatch):
    monkeypatch.setattr(
        detector,
        "scan_devices",
        lambda: [],
    )

    async def run():
        bus = StreamBus()
        received = []

        def handler(event, offset, group_id):
            received.append(
                (event, offset, group_id)
            )

        bus.subscribe(
            "device-agent",
            "DEVICE_DISCONNECTED",
            handler,
        )

        lifecycle_events = detector.detect_lifecycle(
            {"PIXEL_8"}
        )

        assert lifecycle_events == [
            {
                "type": "DEVICE_DISCONNECTED",
                "data": {
                    "serial": "PIXEL_8",
                },
            }
        ]

        await detector.publish_lifecycle_events(
            bus,
            lifecycle_events,
        )

        queued_offset, queued_event = await bus.queue.get()

        assert queued_event.type == "DEVICE_DISCONNECTED"
        assert queued_event.payload == {
            "serial": "PIXEL_8",
        }

        await bus.dispatch(
            queued_offset,
            queued_event,
        )

        assert len(received) == 1

        received_event, received_offset, received_group = received[0]

        assert received_event.type == "DEVICE_DISCONNECTED"
        assert received_event.payload == {
            "serial": "PIXEL_8",
        }
        assert received_offset == queued_offset
        assert received_group == "device-agent"

    asyncio.run(run())
