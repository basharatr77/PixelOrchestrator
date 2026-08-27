from app.core.module_contract import Device, DeviceState, ModuleType

from app.agents.device_agent.adb_detector import scan_adb
from app.agents.device_agent.fastboot_detector import scan_fastboot


def test_adb_detector_returns_canonical_device(monkeypatch):
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

    device = devices[0]

    assert device.device_id == "adb:PIXEL_8"
    assert device.module_type is ModuleType.ADB
    assert device.state is DeviceState.ADB
    assert device.serial == "PIXEL_8"
    assert device.transport == "adb"
    assert device.model == "Pixel 8"
    assert device.properties == {
        "brand": "Google",
        "android_version": "14",
    }


def test_fastboot_detector_returns_canonical_device(monkeypatch):
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

    device = devices[0]

    assert device.device_id == "fastboot:PIXEL_8"
    assert device.module_type is ModuleType.FASTBOOT
    assert device.state is DeviceState.FASTBOOT
    assert device.serial == "PIXEL_8"
    assert device.transport == "fastboot"
