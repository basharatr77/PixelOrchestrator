from app.agents.device_agent.adb_detector import scan_adb
from app.agents.device_agent.fastboot_detector import scan_fastboot
from app.agents.device_agent.device_model import Device


def test_adb_detector_returns_device_objects(monkeypatch):
    def fake_check_output(cmd, text=True):
        assert cmd == ["adb", "devices"]
        return "List of devices attached\nPIXEL_8\tdevice\n"

    monkeypatch.setattr(
        "app.agents.device_agent.adb_detector.subprocess.check_output",
        fake_check_output,
    )

    devices = scan_adb()

    assert len(devices) == 1
    assert isinstance(devices[0], Device)
    assert devices[0].serial == "PIXEL_8"
    assert devices[0].mode == "ADB"


def test_fastboot_detector_returns_device_objects(monkeypatch):
    def fake_check_output(cmd, text=True):
        assert cmd == ["fastboot", "devices"]
        return "PIXEL_8\tfastboot\n"

    monkeypatch.setattr(
        "app.agents.device_agent.fastboot_detector.subprocess.check_output",
        fake_check_output,
    )

    devices = scan_fastboot()

    assert len(devices) == 1
    assert isinstance(devices[0], Device)
    assert devices[0].serial == "PIXEL_8"
    assert devices[0].mode == "FASTBOOT"
