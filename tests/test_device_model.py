from app.core.module_contract import Device, DeviceState, ModuleType


def test_device_minimal_identity():
    device = Device(
        device_id="adb:PIXEL_8",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="PIXEL_8",
        transport="adb",
    )

    assert device.device_id == "adb:PIXEL_8"
    assert device.module_type is ModuleType.ADB
    assert device.state is DeviceState.ADB
    assert device.serial == "PIXEL_8"
    assert device.transport == "adb"


def test_device_optional_metadata():
    device = Device(
        device_id="fastboot:PIXEL_8",
        module_type=ModuleType.FASTBOOT,
        state=DeviceState.FASTBOOT,
        serial="PIXEL_8",
        transport="fastboot",
        model="Pixel 8",
        properties={
            "brand": "Google",
            "android_version": "16",
        },
    )

    assert device.state is DeviceState.FASTBOOT
    assert device.model == "Pixel 8"
    assert device.properties == {
        "brand": "Google",
        "android_version": "16",
    }


def test_device_contract_identity():
    device = Device(
        device_id="adb:PIXEL_8",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="PIXEL_8",
        transport="adb",
    )

    assert device.device_id == "adb:PIXEL_8"
    assert device.module_type is ModuleType.ADB
    assert device.state is DeviceState.ADB
    assert device.serial == "PIXEL_8"
    assert device.transport == "adb"
