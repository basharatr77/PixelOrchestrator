import app.gui.qt_bootstrap
from PyQt6.QtWidgets import QApplication, QLabel

from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType
from app.gui.main_window import MainWindow


def test_device_report_failure_does_not_block_other_health_sections(
    monkeypatch,
):
    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    first = Device(
        device_id="adb:FAIL_REPORT",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="FAIL_REPORT",
        transport="adb",
    )
    second = Device(
        device_id="adb:GOOD_REPORT",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="GOOD_REPORT",
        transport="adb",
    )
    registry.register(first)
    registry.register(second)

    def report_with_one_failure(device):
        if device.device_id == "adb:FAIL_REPORT":
            raise RuntimeError("simulated device report failure")
        return {"device_id": device.device_id}

    monkeypatch.setattr(
        "app.core.device_report.build_device_report",
        report_with_one_failure,
    )

    window = MainWindow(device_registry=registry)
    window.show()
    app.processEvents()

    try:
        window.open_health_center()
        app.processEvents()

        device_health = window._workspaces["health"].findChild(
            QLabel,
            "device_health",
        )
        connection_health = window._workspaces["health"].findChild(
            QLabel,
            "connection_health",
        )

        assert device_health is not None
        assert device_health.property("health_result") == [
            {
                "device_id": "adb:FAIL_REPORT",
                "error": "RuntimeError: simulated device report failure",
            },
            {"device_id": "adb:GOOD_REPORT"},
        ]

        assert connection_health is not None
        assert connection_health.property("health_result") == [
            {
                "device_id": "adb:FAIL_REPORT",
                "serial": "FAIL_REPORT",
                "transport": "adb",
                "state": DeviceState.ADB.value,
            },
            {
                "device_id": "adb:GOOD_REPORT",
                "serial": "GOOD_REPORT",
                "transport": "adb",
                "state": DeviceState.ADB.value,
            },
        ]

        assert window._workspaces["health"].isVisible()
    finally:
        window.close()
