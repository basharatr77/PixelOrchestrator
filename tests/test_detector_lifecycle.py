from app.core.module_contract import Device, DeviceState, ModuleType
from app.agents.device_agent import detector


def test_new_device_generates_connected_event(monkeypatch):
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

    events = detector.detect_lifecycle(set())

    assert events == [
        {
            "type": "DEVICE_CONNECTED",
            "data": {
                "serial": "PIXEL_8",
                "mode": "ADB",
                "brand": "",
                "model": "",
                "android_version": "",
            },
        }
    ]


def test_missing_device_generates_disconnected_event(monkeypatch):
    monkeypatch.setattr(
        detector,
        "scan_devices",
        lambda: [],
    )

    events = detector.detect_lifecycle({"PIXEL_8"})

    assert events == [
        {
            "type": "DEVICE_DISCONNECTED",
            "data": {
                "serial": "PIXEL_8",
            },
        }
    ]


def test_same_device_does_not_generate_duplicate_connected_event(monkeypatch):
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

    events = detector.detect_lifecycle({"PIXEL_8"})

    assert events == []
