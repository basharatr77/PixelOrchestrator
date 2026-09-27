
def test_device_report_builder_returns_canonical_device_data():
    from app.core.module_contract import Device, DeviceState, ModuleType

    from app.core.device_report import build_device_report

    device = Device(
        device_id="adb:TEST123",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        model="RNE-L21",
        serial="TEST123",
        transport="adb",
        properties={
            "brand": "HUAWEI",
            "android_version": "8.0.0",
        },
        capabilities=("diagnostics",),
    )

    report = build_device_report(device)

    assert report["device_id"] == "adb:TEST123"
    assert report["module_type"] == ModuleType.ADB.value
    assert report["state"] == DeviceState.ADB.value
    assert report["model"] == "RNE-L21"
    assert report["serial"] == "TEST123"
    assert report["transport"] == "adb"
    assert report["properties"]["brand"] == "HUAWEI"
    assert report["properties"]["android_version"] == "8.0.0"
    assert report["capabilities"] == ["diagnostics"]

def test_device_report_builder_rejects_non_device():
    from app.core.device_report import build_device_report

    try:
        build_device_report({"device_id": "fake"})
    except TypeError as exc:
        assert str(exc) == "device must be a canonical Device."
    else:
        raise AssertionError("Expected TypeError for non-Device input.")
