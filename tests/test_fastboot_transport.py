from app.core.fastboot_transport import FastbootTransport


class FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_fastboot_transport_connect(monkeypatch):
    def fake_run(cmd, **kwargs):
        assert cmd == [
            "fastboot",
            "-s",
            "RF8T206R8EP",
            "getvar",
            "product",
        ]

        return FakeResult(
            stderr="product: a32\n",
        )

    monkeypatch.setattr(
        "app.core.fastboot_transport.subprocess.run",
        fake_run,
    )

    transport = FastbootTransport("RF8T206R8EP")

    assert transport.connect() is True
    assert transport.is_connected() is True


def test_fastboot_transport_execute(monkeypatch):
    def fake_run(cmd, **kwargs):
        assert cmd == [
            "fastboot",
            "-s",
            "RF8T206R8EP",
            "getvar",
            "product",
        ]

        return FakeResult(
            stderr="product: a32\n",
        )

    monkeypatch.setattr(
        "app.core.fastboot_transport.subprocess.run",
        fake_run,
    )

    transport = FastbootTransport("RF8T206R8EP")

    result = transport.execute(
        ["getvar", "product"]
    )

    assert result["returncode"] == 0
    assert result["stdout"] == ""
    assert result["stderr"] == "product: a32\n"


def test_fastboot_transport_get_device_info(monkeypatch):
    def fake_run(cmd, **kwargs):
        assert cmd == [
            "fastboot",
            "-s",
            "RF8T206R8EP",
            "getvar",
            "product",
        ]

        return FakeResult(
            stderr="product: a32\n",
        )

    monkeypatch.setattr(
        "app.core.fastboot_transport.subprocess.run",
        fake_run,
    )

    transport = FastbootTransport("RF8T206R8EP")

    info = transport.get_device_info()

    assert info == {
        "serial": "RF8T206R8EP",
        "product": "a32",
        "mode": "FASTBOOT",
    }


def test_fastboot_transport_disconnect():
    transport = FastbootTransport("RF8T206R8EP")

    assert transport.disconnect() is True
