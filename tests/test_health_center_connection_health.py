from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType


def test_main_window_health_center_refreshes_connection_health_from_registry():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication, QLabel
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()

    connected = Device(
        device_id="device:CONN_A",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        model="CONN-MODEL-A",
        serial="CONN_A",
        transport="adb",
    )

    disconnected = Device(
        device_id="device:CONN_B",
        module_type=ModuleType.FASTBOOT,
        state=DeviceState.DISCONNECTED,
        model="CONN-MODEL-B",
        serial="CONN_B",
        transport="fastboot",
    )

    registry.register(connected)
    registry.register(disconnected)

    window = MainWindow(device_registry=registry)
    window.show()
    app.processEvents()

    window.open_health_center()
    app.processEvents()

    connection_health = window._workspaces["health"].findChild(
        QLabel,
        "connection_health",
    )

    assert connection_health is not None
    assert connection_health.property("health_result") == [
        {
            "device_id": "device:CONN_A",
            "serial": "CONN_A",
            "transport": "adb",
            "state": DeviceState.ADB.value,
        },
        {
            "device_id": "device:CONN_B",
            "serial": "CONN_B",
            "transport": "fastboot",
            "state": DeviceState.DISCONNECTED.value,
        },
    ]

    window.close()


def test_connection_health_failure_does_not_block_other_devices(monkeypatch):
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication, QLabel
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    malformed = Device(
        device_id="adb:BAD_STATE",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="BAD_STATE",
        transport="adb",
    )
    malformed.state = "INVALID_STATE"

    healthy = Device(
        device_id="adb:HEALTHY",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="HEALTHY",
        transport="adb",
    )

    registry.register(malformed)
    registry.register(healthy)

    window = MainWindow(device_registry=registry)
    window.show()
    app.processEvents()

    try:
        window.open_health_center()
        app.processEvents()

        connection_health = window._workspaces["health"].findChild(
            QLabel,
            "connection_health",
        )

        assert connection_health is not None
        reports = connection_health.property("health_result")

        assert len(reports) == 2
        assert reports[0]["device_id"] == "adb:BAD_STATE"
        assert "error" in reports[0]
        assert reports[1] == {
            "device_id": "adb:HEALTHY",
            "serial": "HEALTHY",
            "transport": "adb",
            "state": DeviceState.ADB.value,
        }
        assert window._workspaces["health"].isVisible()
    finally:
        window.close()
