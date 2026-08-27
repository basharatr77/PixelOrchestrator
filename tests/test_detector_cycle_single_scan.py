import asyncio

from app.agents.device_agent import detector
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.event_bus import StreamBus


def test_detector_cycle_scans_devices_only_once(monkeypatch):
    calls = []

    devices = [
        Device(
                device_id="adb:PIXEL_8",
                module_type=ModuleType.ADB,
                state=DeviceState.ADB,
                serial="PIXEL_8",
                transport="adb",
            )
    ]

    def scan():
        calls.append(1)
        return devices

    monkeypatch.setattr(
        detector,
        "scan_devices",
        scan,
    )

    async def run():
        bus = StreamBus()

        known = {}

        new_known = await detector.run_detector_cycle(
            bus,
            known,
        )

        assert new_known == {
            "PIXEL_8": "ADB",
        }

        assert calls == [1]

    asyncio.run(run())
