import pytest

from app.core.module_contract import (
    Action,
    Capability,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.core.module_loader import ModuleLoader
from app.core.module_registry import ModuleRegistry


class TestModule(ModuleContract):
    manifest = ModuleManifest(
        id="test",
        name="Test",
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
        raise NotImplementedError


class NotAModule:
    pass


class InvalidModule(ModuleContract):
    manifest = ModuleManifest(
        id="invalid",
        name="Invalid",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        capabilities=(
            Capability(
                id="same",
                name="One",
            ),
            Capability(
                id="same",
                name="Duplicate",
            ),
        ),
    )

    def detect(self):
        return []

    def execute(self, action_id, device=None, **kwargs):
        raise NotImplementedError


def test_registry_registers_and_retrieves_module():
    registry = ModuleRegistry()
    module = TestModule()

    registry.register(module)

    assert registry.get("test") is module
    assert registry.has("test")
    assert registry.ids() == ["test"]
    assert registry.modules() == [module]
    assert len(registry) == 1


def test_registry_rejects_duplicate_module_id():
    registry = ModuleRegistry()

    registry.register(TestModule())

    with pytest.raises(
        ValueError,
        match="Module 'test' is already registered",
    ):
        registry.register(TestModule())


def test_registry_rejects_non_contract_object():
    registry = ModuleRegistry()

    with pytest.raises(
        TypeError,
        match="must implement ModuleContract",
    ):
        registry.register(NotAModule())


def test_registry_validates_manifest_before_registration():
    registry = ModuleRegistry()

    with pytest.raises(
        ValueError,
        match="Duplicate capability ID: same",
    ):
        registry.register(InvalidModule())

    assert registry.ids() == []
    assert len(registry) == 0


def test_registry_unregisters_module():
    registry = ModuleRegistry()
    registry.register(TestModule())

    assert registry.unregister("test") is True
    assert registry.get("test") is None
    assert registry.has("test") is False
    assert len(registry) == 0


def test_registry_unregister_missing_module_returns_false():
    registry = ModuleRegistry()

    assert registry.unregister("missing") is False


def test_registry_returns_manifests():
    registry = ModuleRegistry()
    module = TestModule()

    registry.register(module)

    assert registry.manifests() == [module.manifest]


def test_loader_loads_builtin_modules():
    loader = ModuleLoader()

    loaded = loader.load_builtin_modules()

    assert [module.manifest.id for module in loaded] == [
        "common",
        "adb",
    ]

    assert loader.registry.ids() == [
        "common",
        "adb",
    ]

    assert loader.registry.get("common") is loaded[0]
    assert loader.registry.get("adb") is loaded[1]


def test_loader_rejects_non_contract_class():
    loader = ModuleLoader()

    with pytest.raises(
        TypeError,
        match="must implement ModuleContract",
    ):
        loader.load_module(
            "tests.test_module_registry_loader",
            "NotAModule",
        )


def test_loader_loads_custom_contract_module():
    loader = ModuleLoader()

    loaded = loader.load_module(
        "tests.test_module_registry_loader",
        "TestModule",
    )

    assert loaded.manifest.id == "test"
    assert loader.registry.get("test") is loaded
