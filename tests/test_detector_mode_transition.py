from app.agents.device_agent.device_model import Device
from app.agents.device_agent import detector


def test_mode_transition_does_not_disconnect_device(monkeypatch):
    monkeypatch.setattr(
        detector,
        "scan_devices",
        lambda: [
            Device(serial="PIXEL_8", mode="FASTBOOT")
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
