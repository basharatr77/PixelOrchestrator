import pytest

from app.core.module_contract import (
    Action,
    Capability,
    Device,
    DeviceState,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)


def make_manifest(**kwargs):
    defaults = {
        "id": "test",
        "name": "Test",
        "version": "1.0.0",
        "module_type": ModuleType.COMMON,
    }
    defaults.update(kwargs)
    return ModuleManifest(**defaults)


def validate(manifest):
    type(
        "TestModule",
        (ModuleContract,),
        {"manifest": manifest},
    )().validate_manifest()


def test_empty_module_id_is_rejected():
    with pytest.raises(ValueError, match="Module manifest ID cannot be empty"):
        validate(make_manifest(id=""))


def test_empty_capability_id_is_rejected():
    with pytest.raises(ValueError, match="Capability ID cannot be empty"):
        validate(
            make_manifest(
                capabilities=(
                    Capability(id="", name="Broken"),
                )
            )
        )


def test_empty_action_id_is_rejected():
    with pytest.raises(ValueError, match="Action ID cannot be empty"):
        validate(
            make_manifest(
                actions=(
                    Action(id="", name="Broken"),
                )
            )
        )


def test_empty_capability_reference_is_rejected():
    with pytest.raises(
        ValueError,
        match="Action capability ID cannot be empty when provided",
    ):
        validate(
            make_manifest(
                actions=(
                    Action(
                        id="test_action",
                        name="Test",
                        capability_id="   ",
                    ),
                )
            )
        )


def test_duplicate_capability_ids_are_rejected():
    with pytest.raises(
        ValueError,
        match="Duplicate capability ID: same",
    ):
        validate(
            make_manifest(
                capabilities=(
                    Capability(id="same", name="One"),
                    Capability(id="same", name="Two"),
                )
            )
        )


def test_duplicate_action_ids_are_rejected():
    with pytest.raises(
        ValueError,
        match="Duplicate action ID: same",
    ):
        validate(
            make_manifest(
                actions=(
                    Action(id="same", name="One"),
                    Action(id="same", name="Two"),
                )
            )
        )


def test_unknown_capability_reference_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unknown capability ID: missing",
    ):
        validate(
            make_manifest(
                capabilities=(
                    Capability(id="real", name="Real"),
                ),
                actions=(
                    Action(
                        id="test_action",
                        name="Test",
                        capability_id="missing",
                    ),
                ),
            )
        )


def test_canonical_device_identity_and_defaults():
    device = Device(
        device_id="adb:PIXEL_8",
        module_type=ModuleType.ADB,
    )

    assert device.device_id == "adb:PIXEL_8"
    assert device.module_type is ModuleType.ADB
    assert device.state is DeviceState.UNKNOWN
    assert device.model is None
    assert device.serial is None
    assert device.transport is None
    assert device.properties == {}


def test_canonical_device_accepts_runtime_identity():
    device = Device(
        device_id="adb:PIXEL_8",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        model="Pixel 8",
        serial="PIXEL_8",
        transport="adb",
        properties={
            "brand": "Google",
            "android_version": "14",
        },
    )

    assert device.device_id == "adb:PIXEL_8"
    assert device.module_type is ModuleType.ADB
    assert device.state is DeviceState.ADB
    assert device.model == "Pixel 8"
    assert device.serial == "PIXEL_8"
    assert device.transport == "adb"
    assert device.properties == {
        "brand": "Google",
        "android_version": "14",
    }


def test_canonical_device_properties_are_independent():
    first = Device(
        device_id="adb:ONE",
        module_type=ModuleType.ADB,
    )

    second = Device(
        device_id="adb:TWO",
        module_type=ModuleType.ADB,
    )

    first.properties["brand"] = "Google"

    assert first.properties == {"brand": "Google"}
    assert second.properties == {}
