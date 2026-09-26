from app.core.adb_transport import ADBTransport


class FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_adb_transport_connect(monkeypatch):
    def fake_run(cmd, **kwargs):
        assert cmd == [
            "adb",
            "-s",
            "PIXEL_8",
            "get-state",
        ]
        return FakeResult(stdout="device\n")

    monkeypatch.setattr(
        "app.core.adb_transport.subprocess.run",
        fake_run,
    )

    transport = ADBTransport("PIXEL_8")

    assert transport.connect() is True
    assert transport.is_connected() is True


def test_adb_transport_execute(monkeypatch):
    def fake_run(cmd, **kwargs):
        assert cmd == [
            "adb",
            "-s",
            "PIXEL_8",
            "shell",
            "getprop ro.product.model",
        ]

        return FakeResult(
            stdout="Pixel 8\n",
        )

    monkeypatch.setattr(
        "app.core.adb_transport.subprocess.run",
        fake_run,
    )

    transport = ADBTransport("PIXEL_8")

    result = transport.execute(
        "getprop ro.product.model"
    )

    assert result["returncode"] == 0
    assert result["stdout"] == "Pixel 8\n"
    assert result["stderr"] == ""


def test_adb_transport_get_device_info(monkeypatch):
    properties = {
        "ro.product.manufacturer": "samsung\n",
        "ro.product.model": "SM-A525F\n",
        "ro.build.version.release": "14\n",
    }

    def fake_run(cmd, **kwargs):
        prop = cmd[-1]

        assert cmd[:4] == [
            "adb",
            "-s",
            "A52",
            "shell",
        ]

        return FakeResult(
            stdout=properties[prop],
        )

    monkeypatch.setattr(
        "app.core.adb_transport.subprocess.run",
        fake_run,
    )

    transport = ADBTransport("A52")

    info = transport.get_device_info()

    assert info == {
        "serial": "A52",
        "brand": "samsung",
        "model": "SM-A525F",
        "android_version": "14",
    }


def test_adb_transport_disconnect():
    transport = ADBTransport("PIXEL_8")

    assert transport.disconnect() is True

def test_adb_transport_get_firmware_identity(monkeypatch):
    properties = {
        "ro.product.device": "a32",
        "ro.build.id": "AQ3A.240829.003",
        "ro.build.version.release": "15",
        "ro.build.version.security_patch": "2024-09-01",
    }

    def fake_run(cmd, **kwargs):
        prop = cmd[-1]

        assert cmd[:4] == [
            "adb",
            "-s",
            "A52",
            "shell",
        ]

        return FakeResult(
            stdout=properties[prop],
        )

    monkeypatch.setattr(
        "app.core.adb_transport.subprocess.run",
        fake_run,
    )

    transport = ADBTransport("A52")

    identity = transport.get_firmware_identity()

    assert identity == {
        "device_codename": "a32",
        "build_id": "AQ3A.240829.003",
        "android_release": "15",
        "security_patch": "2024-09-01",
    }
