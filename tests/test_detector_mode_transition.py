from app.core.module_contract import Device, DeviceState, ModuleType
from app.agents.device_agent import detector


def test_mode_transition_does_not_disconnect_device(monkeypatch):
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

    events = detector.detect_lifecycle(
        {
            "PIXEL_8": "ADB"
        }
    )

    assert events == [
        {
            "type": "DEVICE_MODE_CHANGED",
            "data": {
                "serial": "PIXEL_8",
                "previous_mode": "ADB",
                "mode": "FASTBOOT",
            },
        }
    ]
