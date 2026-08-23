from app.agents.device_agent.device_model import Device


def test_device_minimal_identity():
    device = Device(
        serial="PIXEL_8",
        mode="ADB",
    )

    assert device.serial == "PIXEL_8"
    assert device.mode == "ADB"


def test_device_optional_metadata():
    device = Device(
        serial="PIXEL_8",
        mode="FASTBOOT",
        brand="Google",
        model="Pixel 8",
        android_version="16",
    )

    assert device.brand == "Google"
    assert device.model == "Pixel 8"
    assert device.android_version == "16"


def test_device_to_dict():
    device = Device(
        serial="PIXEL_8",
        mode="ADB",
        brand="Google",
        model="Pixel 8",
    )

    data = device.to_dict()

    assert data["serial"] == "PIXEL_8"
    assert data["mode"] == "ADB"
    assert data["brand"] == "Google"
    assert data["model"] == "Pixel 8"
