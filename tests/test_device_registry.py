from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType


def make_device(
    device_id="pixel-8",
    serial="PIXEL_8",
    state=DeviceState.ADB,
):
    return Device(
        device_id=device_id,
        module_type=ModuleType.ADB,
        state=state,
        model="Pixel 8",
        serial=serial,
        transport="adb",
    )


def test_register_and_get_device():
    registry = DeviceRegistry()
    device = make_device()

    registry.register(device)

    assert registry.get("pixel-8") is device
    assert registry.contains("pixel-8")


def test_register_rejects_duplicate_device_id():
    registry = DeviceRegistry()

    registry.register(make_device())

    try:
        registry.register(make_device())
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("Duplicate device_id was accepted")


def test_update_replaces_existing_device():
    registry = DeviceRegistry()

    original = make_device(state=DeviceState.ADB)
    updated = make_device(state=DeviceState.FASTBOOT)

    registry.register(original)
    registry.update(updated)

    assert registry.get("pixel-8") is updated
    assert registry.get("pixel-8").state == DeviceState.FASTBOOT


def test_remove_device():
    registry = DeviceRegistry()
    registry.register(make_device())

    assert registry.remove("pixel-8") is True
    assert registry.get("pixel-8") is None
    assert registry.contains("pixel-8") is False


def test_remove_missing_device_returns_false():
    registry = DeviceRegistry()

    assert registry.remove("missing") is False


def test_snapshot_returns_registered_devices():
    registry = DeviceRegistry()

    first = make_device("pixel-8", "PIXEL_8")
    second = make_device("pixel-7", "PIXEL_7")

    registry.register(first)
    registry.register(second)

    snapshot = registry.snapshot()

    assert snapshot == {
        "pixel-8": first,
        "pixel-7": second,
    }


def test_snapshot_does_not_expose_internal_registry():
    registry = DeviceRegistry()
    device = make_device()

    registry.register(device)

    snapshot = registry.snapshot()
    snapshot.pop("pixel-8")

    assert registry.contains("pixel-8")


def test_clear_removes_all_devices():
    registry = DeviceRegistry()

    registry.register(make_device("pixel-8"))
    registry.register(make_device("pixel-7"))

    registry.clear()

    assert registry.snapshot() == {}
