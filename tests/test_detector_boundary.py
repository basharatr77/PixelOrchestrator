from app.agents.device_agent import detector
from app.agents.device_agent.device_model import Device


def test_detector_uses_canonical_detectors(monkeypatch):
    adb_devices = [
        Device(serial="PIXEL_8", mode="ADB")
    ]

    fastboot_devices = [
        Device(serial="PIXEL_7", mode="FASTBOOT")
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
