from app.agents.device_agent.adb_detector import scan_adb
from app.agents.device_agent.fastboot_detector import scan_fastboot
from app.agents.device_agent.device_model import Device


def test_adb_detector_returns_device_objects(monkeypatch):
    def fake_check_output(cmd, text=True, timeout=5):
        if cmd == ["adb", "devices"]:
            return "List of devices attached\nPIXEL_8\tdevice\n"

        if cmd == [
            "adb",
            "-s",
            "PIXEL_8",
            "shell",
            "getprop",
            "ro.product.manufacturer",
        ]:
            return "Google\n"

        if cmd == [
            "adb",
            "-s",
            "PIXEL_8",
            "shell",
            "getprop",
            "ro.product.model",
        ]:
            return "Pixel 8\n"

        if cmd == [
            "adb",
            "-s",
            "PIXEL_8",
            "shell",
            "getprop",
            "ro.build.version.release",
        ]:
            return "14\n"

        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(
        "app.agents.device_agent.adb_detector.subprocess.check_output",
        fake_check_output,
    )

    devices = scan_adb()

    assert len(devices) == 1
    assert isinstance(devices[0], Device)
    assert devices[0].serial == "PIXEL_8"
    assert devices[0].mode == "ADB"
    assert devices[0].brand == "Google"
    assert devices[0].model == "Pixel 8"
    assert devices[0].android_version == "14"


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
