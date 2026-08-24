import pytest

from app.agents.device_agent.device_model import Device
from app.core.adb_transport import ADBTransport
from app.core.fastboot_transport import FastbootTransport
from app.core.transport_resolver import TransportResolver


def test_resolver_returns_adb_transport():
    device = Device(
        serial="A52",
        mode="ADB",
        brand="samsung",
        model="SM-A525F",
        android_version="14",
    )

    transport = TransportResolver.resolve(device)

    assert isinstance(transport, ADBTransport)
    assert transport.serial == "A52"


def test_resolver_returns_fastboot_transport():
    device = Device(
        serial="RF8T206R8EP",
        mode="FASTBOOT",
    )

    transport = TransportResolver.resolve(device)

    assert isinstance(transport, FastbootTransport)
    assert transport.serial == "RF8T206R8EP"


def test_resolver_rejects_missing_device():
    with pytest.raises(ValueError, match="device"):
        TransportResolver.resolve(None)
