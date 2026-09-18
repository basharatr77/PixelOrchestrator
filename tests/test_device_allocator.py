import pytest

from app.core.device_registry import DeviceRegistry
from app.core.device_allocator import DeviceAllocator
from app.core.module_contract import Device, DeviceState, ModuleType


def make_device(device_id, serial, state=DeviceState.ADB):
    return Device(
        device_id=device_id,
        module_type=ModuleType.ADB,
        state=state,
        model="Pixel",
        serial=serial,
    )


def test_device_allocator_selects_deterministically_from_eligible_devices():
    registry = DeviceRegistry()
    registry.register(make_device("device:B", "B"))
    registry.register(make_device("device:A", "A"))

    allocator = DeviceAllocator(registry)

    assert allocator.select() == "device:A"


def test_device_allocator_rejects_when_no_eligible_device_exists():
    registry = DeviceRegistry()
    registry.register(
        make_device(
            "device:OFFLINE",
            "OFFLINE",
            state=DeviceState.DISCONNECTED,
        )
    )

    allocator = DeviceAllocator(registry)

    with pytest.raises(RuntimeError, match="No eligible device"):
        allocator.select()

def test_device_allocator_requires_canonical_registry():
    with pytest.raises(TypeError, match="registry must be a DeviceRegistry"):
        DeviceAllocator(None)

def test_device_allocator_ignores_non_adb_devices():
    registry = DeviceRegistry()
    registry.register(
        make_device(
            "device:FASTBOOT",
            "FASTBOOT",
            state=DeviceState.FASTBOOT,
        )
    )
    registry.register(
        make_device(
            "device:ADB",
            "ADB",
            state=DeviceState.ADB,
        )
    )

    allocator = DeviceAllocator(registry)

    assert allocator.select() == "device:ADB"
