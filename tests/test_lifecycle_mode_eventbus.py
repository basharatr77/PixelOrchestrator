import asyncio

from app.agents.device_agent import detector
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.event_bus import StreamBus


def test_device_mode_changed_lifecycle_reaches_subscriber(monkeypatch):
    monkeypatch.setattr(
        detector,
        "scan_devices",
        lambda: [
            Device(
                device_id="fastboot:PIXEL_8",
                module_type=ModuleType.FASTBOOT,
                state=DeviceState.FASTBOOT,
                serial="PIXEL_8",
                transport="fastboot",
            )
        ],
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
            "DEVICE_MODE_CHANGED",
            handler,
        )

        lifecycle_events = detector.detect_lifecycle(
            {"PIXEL_8": "ADB"}
        )

        assert lifecycle_events == [
            {
                "type": "DEVICE_MODE_CHANGED",
                "data": {
                    "serial": "PIXEL_8",
                    "previous_mode": "ADB",
                    "mode": "FASTBOOT",
                },
            }
        ]

        await detector.publish_lifecycle_events(
            bus,
            lifecycle_events,
        )

        queued_offset, queued_event = await bus.queue.get()

        assert queued_event.type == "DEVICE_MODE_CHANGED"
        assert queued_event.payload == {
            "serial": "PIXEL_8",
            "previous_mode": "ADB",
            "mode": "FASTBOOT",
        }

        await bus.dispatch(
            queued_offset,
            queued_event,
        )

        assert len(received) == 1

        received_event, received_offset, received_group = received[0]

        assert received_event.type == "DEVICE_MODE_CHANGED"
        assert received_event.payload == {
            "serial": "PIXEL_8",
            "previous_mode": "ADB",
            "mode": "FASTBOOT",
        }
        assert received_offset == queued_offset
        assert received_group == "device-agent"

    asyncio.run(run())
