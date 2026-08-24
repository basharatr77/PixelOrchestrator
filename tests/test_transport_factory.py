import pytest

from app.core.adb_transport import ADBTransport
from app.core.fastboot_transport import FastbootTransport
from app.core.transport_factory import TransportFactory


def test_factory_returns_adb_transport():
    transport = TransportFactory.create(
        serial="A52",
        mode="ADB",
    )

    assert isinstance(transport, ADBTransport)
    assert transport.serial == "A52"


def test_factory_returns_fastboot_transport():
    transport = TransportFactory.create(
        serial="RF8T206R8EP",
        mode="FASTBOOT",
    )

    assert isinstance(transport, FastbootTransport)
    assert transport.serial == "RF8T206R8EP"


def test_factory_rejects_unsupported_mode():
    with pytest.raises(ValueError, match="Unsupported transport mode"):
        TransportFactory.create(
            serial="TEST",
            mode="EDL",
        )


def test_factory_requires_serial():
    with pytest.raises(ValueError, match="serial"):
        TransportFactory.create(
            serial="",
            mode="ADB",
        )
