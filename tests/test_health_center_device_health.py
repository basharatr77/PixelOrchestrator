from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType


def test_main_window_health_center_refreshes_device_health_from_registry():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication, QLabel
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    device_a = Device(
        device_id="adb:HEALTH_A",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        model="HEALTH-MODEL-A",
        serial="HEALTH_A",
        transport="adb",
        properties={"brand": "TEST"},
        capabilities=("diagnostics",),
    )
    device_b = Device(
        device_id="fastboot:HEALTH_B",
        module_type=ModuleType.FASTBOOT,
        state=DeviceState.FASTBOOT,
        model="HEALTH-MODEL-B",
        serial="HEALTH_B",
        transport="fastboot",
    )

    registry.register(device_a)
    registry.register(device_b)

    window = MainWindow(device_registry=registry)
    window.show()
    app.processEvents()

    window.open_health_center()
    app.processEvents()

    device_health = window._workspaces["health"].findChild(
        QLabel,
        "device_health",
    )

    assert device_health is not None
    assert device_health.property("health_result") == [
        {
            "device_id": "adb:HEALTH_A",
            "module_type": ModuleType.ADB.value,
            "state": DeviceState.ADB.value,
            "model": "HEALTH-MODEL-A",
            "serial": "HEALTH_A",
            "transport": "adb",
            "properties": {"brand": "TEST"},
            "capabilities": ["diagnostics"],
        },
        {
            "device_id": "fastboot:HEALTH_B",
            "module_type": ModuleType.FASTBOOT.value,
            "state": DeviceState.FASTBOOT.value,
            "model": "HEALTH-MODEL-B",
            "serial": "HEALTH_B",
            "transport": "fastboot",
            "properties": {},
            "capabilities": [],
        },
    ]

    assert registry.snapshot() == {
        "adb:HEALTH_A": device_a,
        "fastboot:HEALTH_B": device_b,
    }

    window.close()
