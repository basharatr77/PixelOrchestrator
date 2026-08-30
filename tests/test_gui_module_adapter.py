from app.core.module_contract import (
    Action,
    Capability,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.core.module_registry import ModuleRegistry
from app.gui.module_adapter import GUIModuleAdapter


class TestModule(ModuleContract):
    manifest = ModuleManifest(
        id="test",
        name="Test",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        description="Test module",
        capabilities=(
            Capability(
                id="test_capability",
                name="Test Capability",
                description="Test capability description",
            ),
        ),
        actions=(
            Action(
                id="test_action",
                name="Test Action",
                description="Test action description",
                capability_id="test_capability",
                requires_device=True,
                dangerous=False,
                enabled=True,
            ),
        ),
    )

    def detect(self):
        return []

    def execute(self, action_id, device=None, **kwargs):
        raise NotImplementedError


def test_adapter_loads_builtin_modules():
    adapter = GUIModuleAdapter()

    adapter.load_modules()

    assert adapter.registry.ids() == [
        "common",
        "adb",
    ]


def test_adapter_returns_module_metadata():
    adapter = GUIModuleAdapter()

    adapter.load_modules()

    modules = adapter.get_modules()

    assert modules == [
        {
            "id": "common",
            "name": "Common",
            "version": "1.0.0",
            "type": "common",
            "description": "Common device and orchestration functionality.",
        },
        {
            "id": "adb",
            "name": "ADB",
            "version": "1.0.0",
            "type": "adb",
            "description": (
                "Android Debug Bridge device management and operations."
            ),
        },
    ]


def test_adapter_returns_capabilities():
    adapter = GUIModuleAdapter()

    adapter.registry.register(TestModule())

    capabilities = adapter.get_capabilities("test")

    assert len(capabilities) == 1
    assert capabilities[0].id == "test_capability"
    assert capabilities[0].name == "Test Capability"
    assert capabilities[0].description == "Test capability description"


def test_adapter_returns_empty_capabilities_for_unknown_module():
    adapter = GUIModuleAdapter()

    assert adapter.get_capabilities("missing") == []


def test_adapter_returns_actions():
    adapter = GUIModuleAdapter()

    adapter.registry.register(TestModule())

    actions = adapter.get_actions("test")

    assert len(actions) == 1
    assert actions[0].id == "test_action"
    assert actions[0].name == "Test Action"
    assert actions[0].capability_id == "test_capability"


def test_adapter_returns_empty_actions_for_unknown_module():
    adapter = GUIModuleAdapter()

    assert adapter.get_actions("missing") == []


def test_adapter_returns_gui_action_buttons():
    adapter = GUIModuleAdapter()

    adapter.registry.register(TestModule())

    buttons = adapter.get_action_buttons("test")

    assert buttons == [
        {
            "id": "test_action",
            "name": "Test Action",
            "description": "Test action description",
            "capability_id": "test_capability",
            "requires_device": True,
            "dangerous": False,
            "enabled": True,
        }
    ]


def test_adapter_returns_empty_action_buttons_for_unknown_module():
    adapter = GUIModuleAdapter()

    assert adapter.get_action_buttons("missing") == []
