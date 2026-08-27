import pytest

from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.adb_transport import ADBTransport
from app.core.fastboot_transport import FastbootTransport
from app.core.transport_resolver import TransportResolver


def test_resolver_returns_adb_transport():
    device = Device(
        device_id="adb:A52",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="A52",
        model="SM-A525F",
        properties={
            "brand": "samsung",
            "android_version": "14",
        },
    )

    transport = TransportResolver.resolve(device)

    assert isinstance(transport, ADBTransport)
    assert transport.serial == "A52"


def test_resolver_returns_fastboot_transport():
    device = Device(
        device_id="fastboot:RF8T206R8EP",
        module_type=ModuleType.FASTBOOT,
        state=DeviceState.FASTBOOT,
        serial="RF8T206R8EP",
    )

    transport = TransportResolver.resolve(device)

    assert isinstance(transport, FastbootTransport)
    assert transport.serial == "RF8T206R8EP"


def test_resolver_rejects_missing_device():
    with pytest.raises(ValueError, match="device"):
        TransportResolver.resolve(None)
