from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.gui.module_adapter import GUIModuleAdapter


class AuthorizationModule(ModuleContract):
    manifest = ModuleManifest(
        id="auth_test",
        name="Authorization Test",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        capabilities=(
            Capability(
                id="disabled_cap",
                name="Disabled Capability",
                enabled=False,
            ),
        ),
        actions=(
            Action(
                id="disabled_action",
                name="Disabled Action",
                capability_id="disabled_cap",
                enabled=True,
            ),
            Action(
                id="action_disabled",
                name="Action Disabled",
                capability_id="disabled_cap",
                enabled=False,
            ),
        ),
    )

    def detect(self):
        return []

    def execute(self, action_id, device=None, **kwargs):
        return ActionResult(success=True, message="EXECUTED")


def test_disabled_action_is_rejected_before_module_execute():
    adapter = GUIModuleAdapter()
    adapter.registry.register(AuthorizationModule())

    result = adapter.execute_action("auth_test", "action_disabled")

    assert result.success is False
    assert result.error_code == "ACTION_DISABLED"


def test_disabled_capability_is_rejected_before_module_execute():
    adapter = GUIModuleAdapter()
    adapter.registry.register(AuthorizationModule())

    result = adapter.execute_action("auth_test", "disabled_action")

    assert result.success is False
    assert result.error_code == "CAPABILITY_DISABLED"

def test_device_required_action_is_rejected_without_device():
    adapter = GUIModuleAdapter()
    module = AuthorizationModule()
    module.manifest = ModuleManifest(
        id="device_required_test",
        name="Device Required Test",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        capabilities=(
            Capability(id="device_cap", name="Device Capability"),
        ),
        actions=(
            Action(
                id="device_action",
                name="Device Action",
                capability_id="device_cap",
                requires_device=True,
            ),
        ),
    )
    adapter.registry.register(module)

    result = adapter.execute_action("device_required_test", "device_action")

    assert result.success is False
    assert result.error_code == "DEVICE_REQUIRED"

def test_disallowed_transport_is_rejected():
    adapter = GUIModuleAdapter()
    module = AuthorizationModule()
    module.manifest = ModuleManifest(
        id="transport_test",
        name="Transport Test",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        capabilities=(
            Capability(id="transport_cap", name="Transport Capability"),
        ),
        actions=(
            Action(
                id="transport_action",
                name="Transport Action",
                capability_id="transport_cap",
                requires_device=True,
                allowed_transports=("adb",),
            ),
        ),
    )
    adapter.registry.register(module)

    from app.core.module_contract import Device

    device = Device(
        device_id="test-device",
        module_type=ModuleType.COMMON,
        transport="fastboot",
    )

    result = adapter.execute_action(
        "transport_test",
        "transport_action",
        device=device,
    )

    assert result.success is False
    assert result.error_code == "TRANSPORT_NOT_ALLOWED"

def test_disallowed_device_state_is_rejected():
    adapter = GUIModuleAdapter()
    module = AuthorizationModule()
    module.manifest = ModuleManifest(
        id="state_test",
        name="State Test",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        capabilities=(
            Capability(id="state_cap", name="State Capability"),
        ),
        actions=(
            Action(
                id="state_action",
                name="State Action",
                capability_id="state_cap",
                requires_device=True,
                allowed_states=("ready",),
            ),
        ),
    )
    adapter.registry.register(module)

    from app.core.module_contract import Device, DeviceState

    device = Device(
        device_id="test-device",
        module_type=ModuleType.COMMON,
        state=DeviceState.UNKNOWN,
        transport="adb",
    )

    result = adapter.execute_action(
        "state_test",
        "state_action",
        device=device,
    )

    assert result.success is False
    assert result.error_code == "STATE_NOT_ALLOWED"
