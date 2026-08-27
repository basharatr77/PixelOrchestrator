from app.agents.device_agent import detector
from app.core.module_contract import Device, DeviceState, ModuleType


def test_detector_uses_canonical_detectors(monkeypatch):
    adb_devices = [
        Device(
                device_id="adb:PIXEL_8",
                module_type=ModuleType.ADB,
                state=DeviceState.ADB,
                serial="PIXEL_8",
                transport="adb",
            )
    ]

    fastboot_devices = [
        Device(
                device_id="fastboot:PIXEL_7",
                module_type=ModuleType.FASTBOOT,
                state=DeviceState.FASTBOOT,
                serial="PIXEL_7",
                transport="fastboot",
            )
    ]

    monkeypatch.setattr(
        detector,
        "scan_adb",
        lambda: adb_devices,
    )

    monkeypatch.setattr(
        detector,
        "scan_fastboot",
        lambda: fastboot_devices,
    )

    devices = detector.scan_devices()

    assert devices == adb_devices + fastboot_devices
    assert all(isinstance(device, Device) for device in devices)
