from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.gui.module_adapter import GUIModuleAdapter


class DangerousApprovalTestModule(ModuleContract):
    manifest = ModuleManifest(
        id="phase49_dangerous_test",
        name="Phase 49 Dangerous Approval Test",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        description="Regression tests for dangerous-action approval.",
        capabilities=(
            Capability(
                id="dangerous_test_capability",
                name="Dangerous Test Capability",
            ),
        ),
        actions=(
            Action(
                id="dangerous_action_a",
                name="Dangerous Action A",
                capability_id="dangerous_test_capability",
                requires_device=False,
                dangerous=True,
            ),
            Action(
                id="dangerous_action_b",
                name="Dangerous Action B",
                capability_id="dangerous_test_capability",
                requires_device=False,
                dangerous=True,
            ),
        ),
    )

    def __init__(self):
        self.executed_actions = []

    def detect(self):
        return []

    def execute(self, action_id, device=None, **kwargs):
        self.executed_actions.append(action_id)
        return ActionResult(
            success=True,
            message="Test action executed.",
        )


def make_adapter_and_module():
    adapter = GUIModuleAdapter()
    module = DangerousApprovalTestModule()
    adapter.registry.register(module)
    return adapter, module


def test_dangerous_action_is_rejected_without_approval():
    adapter, module = make_adapter_and_module()

    result = adapter.execute_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
    )

    assert result.success is False
    assert result.error_code == "DANGEROUS_ACTION_REQUIRES_APPROVAL"
    assert module.executed_actions == []


def test_dangerous_action_approval_can_be_used_only_once():
    adapter, module = make_adapter_and_module()

    token = adapter.approve_dangerous_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
    )

    first_result = adapter.execute_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
        approval_token=token,
    )
    second_result = adapter.execute_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
        approval_token=token,
    )

    assert first_result.success is True
    assert second_result.success is False
    assert second_result.error_code == "DANGEROUS_ACTION_REQUIRES_APPROVAL"
    assert module.executed_actions == ["dangerous_action_a"]


def test_dangerous_action_approval_is_scoped_to_exact_action():
    adapter, module = make_adapter_and_module()

    token = adapter.approve_dangerous_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
    )

    result_b = adapter.execute_action(
        "phase49_dangerous_test",
        "dangerous_action_b",
        approval_token=token,
    )
    result_a = adapter.execute_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
        approval_token=token,
    )

    assert result_b.success is False
    assert result_b.error_code == "DANGEROUS_ACTION_REQUIRES_APPROVAL"
    assert result_a.success is True
    assert module.executed_actions == ["dangerous_action_a"]


def test_gui_yes_confirmation_uses_real_adapter_approval(monkeypatch):
    import app.gui.qt_bootstrap
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from app.core.device_registry import DeviceRegistry
    from app.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(device_registry=DeviceRegistry())
    module = DangerousApprovalTestModule()
    window.module_adapter.registry.register(module)

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    try:
        window.execute_module_action(
            "phase49_dangerous_test",
            "dangerous_action_a",
        )
        app.processEvents()

        assert module.executed_actions == ["dangerous_action_a"]
        assert window.module_adapter._dangerous_action_approvals == {}
    finally:
        window.close()
        app.processEvents()


def test_dangerous_action_approval_is_bound_to_device():
    from app.core.module_contract import Device

    adapter, module = make_adapter_and_module()
    device_a = Device(
        device_id="device-A",
        module_type=ModuleType.COMMON,
    )
    device_b = Device(
        device_id="device-B",
        module_type=ModuleType.COMMON,
    )

    token = adapter.approve_dangerous_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
        device=device_a,
    )

    wrong_device_result = adapter.execute_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
        device=device_b,
        approval_token=token,
    )
    correct_device_result = adapter.execute_action(
        "phase49_dangerous_test",
        "dangerous_action_a",
        device=device_a,
        approval_token=token,
    )

    assert wrong_device_result.success is False
    assert wrong_device_result.error_code == "DANGEROUS_ACTION_REQUIRES_APPROVAL"
    assert correct_device_result.success is True
    assert module.executed_actions == ["dangerous_action_a"]
    assert adapter._dangerous_action_approvals == {}
