import asyncio

from app.agents.device_agent import detector
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.event_bus import StreamBus


def test_detector_cycle_publishes_lifecycle_events(monkeypatch):
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
        received = []

        def handler(event, offset, group_id):
            received.append(
                (event, offset, group_id)
            )

        bus.subscribe(
            "device-agent",
            "DEVICE_CONNECTED",
            handler,
        )

        known = {}

        new_known = await detector.run_detector_cycle(
            bus,
            known,
        )

        assert new_known == {
            "PIXEL_8": "ADB",
        }

        queued_offset, queued_event = await bus.queue.get()

        await bus.dispatch(
            queued_offset,
            queued_event,
        )

        assert len(received) == 1
        assert received[0][0].type == "DEVICE_CONNECTED"
        assert received[0][0].payload == {
            "serial": "PIXEL_8",
            "mode": "ADB",
            "brand": "",
            "model": "",
            "android_version": "",
        }

    asyncio.run(run())
