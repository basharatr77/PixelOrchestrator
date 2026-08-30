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
