
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

def test_device_report_export_writes_json_file(tmp_path):
    from app.core.module_contract import Device, DeviceState, ModuleType
    from app.core.device_report import export_device_report

    device = Device(
        device_id="adb:EXPORTTEST",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        model="EXPORT-MODEL",
        serial="EXPORTTEST",
        transport="adb",
    )

    output_path = tmp_path / "device_report.json"
    export_device_report(device, output_path)

    assert output_path.exists()
    assert '"device_id": "adb:EXPORTTEST"' in output_path.read_text()

def test_device_report_pdf_export_writes_file(tmp_path):
    from app.core.module_contract import Device, DeviceState, ModuleType
    from app.core.device_report import export_device_report_pdf

    device = Device(
        device_id="adb:PDFTEST",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        model="PDF-MODEL",
        serial="PDFTEST",
        transport="adb",
    )

    output_path = tmp_path / "device_report.pdf"
    export_device_report_pdf(device, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_device_report_pdf_contains_device_data(tmp_path):
    import app.gui.qt_bootstrap
    from PyQt6.QtPdf import QPdfDocument
    from app.core.module_contract import Device, DeviceState, ModuleType
    from app.core.device_report import export_device_report_pdf

    device = Device(
        device_id="adb:PDFCONTENT",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        model="CONTENT-MODEL",
        serial="PDFCONTENT",
        transport="adb",
    )

    output_path = tmp_path / "device_report_content.pdf"
    export_device_report_pdf(device, output_path)

    document = QPdfDocument(None)
    assert document.load(str(output_path)) == QPdfDocument.Error.None_
    assert document.pageCount() == 1

    text = document.getAllText(0).text()
    assert "PixelOrchestrator Device Report" in text
    assert "adb:PDFCONTENT" in text
    assert "CONTENT-MODEL" in text
    assert "PDFCONTENT" in text
