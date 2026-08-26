"""Module Loader V1 for PixelOrchestrator.

Discovers and loads PixelOrchestrator modules without putting
vendor-specific implementation logic inside the registry.
"""

import importlib
from typing import Iterable

from app.core.module_contract import ModuleContract
from app.core.module_registry import ModuleRegistry


class ModuleLoader:
    """Discover and register PixelOrchestrator modules."""

    def __init__(self, registry: ModuleRegistry | None = None) -> None:
        self.registry = registry or ModuleRegistry()

    def load_module(self, module_path: str, class_name: str) -> ModuleContract:
        """Import a module class, instantiate it, and register it."""

        imported = importlib.import_module(module_path)
        module_class = getattr(imported, class_name)

        module = module_class()

        if not isinstance(module, ModuleContract):
            raise TypeError(
                f"{module_path}.{class_name} must implement ModuleContract."
            )

        self.registry.register(module)
        return module

    def load_modules(
        self,
        modules: Iterable[tuple[str, str]],
    ) -> list[ModuleContract]:
        """Load and register multiple modules."""

        loaded = []

        for module_path, class_name in modules:
            loaded.append(
                self.load_module(module_path, class_name)
            )

        return loaded

    def load_builtin_modules(self) -> list[ModuleContract]:
        """Load currently available built-in modules."""

        return self.load_modules(
            [
                (
                    "app.modules.common.module",
                    "CommonModule",
                ),
                (
                    "app.modules.adb.module",
                    "ADBModule",
                ),
            ]
        )
