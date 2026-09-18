from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    Device,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.gui.module_adapter import GUIModuleAdapter


class TestExecutableModule(ModuleContract):
    manifest = ModuleManifest(
        id="test_exec",
        name="Test Executable",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        capabilities=(
            Capability(
                id="test_capability",
                name="Test Capability",
            ),
        ),
        actions=(
            Action(
                id="test_action",
                name="Test Action",
                capability_id="test_capability",
            ),
        ),
    )

    def detect(self):
        return []

    def execute(self, action_id, device=None, **kwargs):
        return ActionResult(
            success=True,
            message="Test action executed.",
            data={
                "action_id": action_id,
                "device_id": device.device_id if device else None,
                "kwargs": kwargs,
            },
        )


def test_adapter_executes_registered_module_action():
    adapter = GUIModuleAdapter()
    adapter.registry.register(TestExecutableModule())

    device = Device(
        device_id="test:001",
        module_type=ModuleType.COMMON,
    )

    result = adapter.execute_action(
        "test_exec",
        "test_action",
        device=device,
        sample="value",
    )

    assert isinstance(result, ActionResult)
    assert result.success is True
    assert result.message == "Test action executed."
    assert result.data["action_id"] == "test_action"
    assert result.data["device_id"] == "test:001"
    assert result.data["kwargs"]["sample"] == "value"


def test_adapter_returns_failure_for_unknown_module_action():
    adapter = GUIModuleAdapter()

    result = adapter.execute_action(
        "missing",
        "test_action",
    )

    assert isinstance(result, ActionResult)
    assert result.success is False
    assert result.error_code == "MODULE_NOT_FOUND"


def test_dynamic_gui_button_click_invokes_correct_module_action():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    window = MainWindow()

    captured = []

    def capture(module_id, action_id):
        captured.append((module_id, action_id))

    window.execute_module_action = capture

    button = window.module_action_buttons["common"]["refresh_devices"]

    assert button.isEnabled() is True
    assert button.receivers(button.clicked) == 1

    button.click()
    app.processEvents()

    assert captured == [("common", "refresh_devices")]

    window.close()

def test_main_window_dispatches_device_required_action_to_selected_canonical_device():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    device = Device(
        device_id="test:gui-selected",
        module_type=ModuleType.COMMON,
    )
    registry.register(device)

    window = MainWindow(device_registry=registry)
    window.selected_device_id = "test:gui-selected"

    captured = {}

    def capture(module_id, action_id, device=None):
        captured["module_id"] = module_id
        captured["action_id"] = action_id
        captured["device"] = device
        return ActionResult(success=True, message="captured")

    window.module_adapter.execute_action = capture

    window.execute_module_action("common", "device_info")

    app.processEvents()

    assert captured["module_id"] == "common"
    assert captured["action_id"] == "device_info"
    assert captured["device"] is device

    window.close()
def test_main_window_rejects_device_required_action_without_selected_device():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    window = MainWindow(device_registry=registry)

    captured = []

    def capture(*args, **kwargs):
        captured.append((args, kwargs))
        return ActionResult(success=True, message="should not execute")

    window.module_adapter.execute_action = capture

    window.execute_module_action("common", "device_info")

    app.processEvents()

    assert captured == []

    window.close()
def test_main_window_rejects_stale_selected_device():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    window = MainWindow(device_registry=registry)
    window.selected_device_id = "stale:missing"

    captured = []

    def capture(*args, **kwargs):
        captured.append((args, kwargs))
        return ActionResult(success=True, message="should not execute")

    window.module_adapter.execute_action = capture

    window.execute_module_action("common", "device_info")

    app.processEvents()

    assert captured == []

    window.close()
def test_main_window_populates_device_selector_from_canonical_registry():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    registry.register(
        Device(
            device_id="test:gui-device",
            module_type=ModuleType.COMMON,
        )
    )

    window = MainWindow(device_registry=registry)

    assert window.device_selector.count() == 1
    assert window.device_selector.itemData(0) == "test:gui-device"

    window.close()
def test_main_window_device_selector_updates_selected_device_id():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    registry.register(
        Device(
            device_id="test:first-device",
            module_type=ModuleType.COMMON,
        )
    )
    registry.register(
        Device(
            device_id="test:second-device",
            module_type=ModuleType.COMMON,
        )
    )

    window = MainWindow(device_registry=registry)

    window.device_selector.setCurrentIndex(1)
    app.processEvents()

    assert window.selected_device_id == "test:second-device"

    window.close()
def test_main_window_refreshes_device_selector_from_current_registry():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    registry.register(
        Device(
            device_id="test:initial-device",
            module_type=ModuleType.COMMON,
        )
    )

    window = MainWindow(device_registry=registry)

    registry.register(
        Device(
            device_id="test:new-device",
            module_type=ModuleType.COMMON,
        )
    )

    window.refresh_device_selector()

    assert window.device_selector.count() == 2
    assert window.device_selector.itemData(0) == "test:initial-device"
    assert window.device_selector.itemData(1) == "test:new-device"

    window.close()
def test_main_window_refresh_preserves_existing_selected_device():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    registry.register(
        Device(
            device_id="test:first-device",
            module_type=ModuleType.COMMON,
        )
    )
    registry.register(
        Device(
            device_id="test:selected-device",
            module_type=ModuleType.COMMON,
        )
    )

    window = MainWindow(device_registry=registry)
    window.device_selector.setCurrentIndex(1)
    app.processEvents()

    assert window.selected_device_id == "test:selected-device"

    window.refresh_device_selector()

    assert window.selected_device_id == "test:selected-device"
    assert window.device_selector.currentData() == "test:selected-device"

    window.close()
def test_main_window_refresh_clears_removed_selected_device():
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    registry = DeviceRegistry()
    registry.register(
        Device(
            device_id="test:remaining-device",
            module_type=ModuleType.COMMON,
        )
    )
    registry.register(
        Device(
            device_id="test:removed-device",
            module_type=ModuleType.COMMON,
        )
    )

    window = MainWindow(device_registry=registry)
    window.device_selector.setCurrentIndex(1)
    app.processEvents()

    assert window.selected_device_id == "test:removed-device"

    registry.remove("test:removed-device")
    window.refresh_device_selector()

    assert window.selected_device_id != "test:removed-device"
    assert window.device_selector.currentData() == "test:remaining-device"

    window.close()
