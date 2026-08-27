"""Module Registry v1 for PixelOrchestrator.

The registry provides a central, vendor-neutral catalog of modules.
It does not contain vendor-specific implementation logic.
"""

from typing import Iterator

from app.core.module_contract import ModuleContract, ModuleManifest


class ModuleRegistry:
    """Central registry for PixelOrchestrator modules."""

    def __init__(self) -> None:
        self._modules: dict[str, ModuleContract] = {}

    def register(self, module: ModuleContract) -> None:
        """Validate and register a module using its manifest ID."""
        if not isinstance(module, ModuleContract):
            raise TypeError("Module must implement ModuleContract.")

        module.validate_manifest()
        module_id = module.manifest.id

        if module_id in self._modules:
            raise ValueError(
                f"Module '{module_id}' is already registered."
            )

        self._modules[module_id] = module

    def unregister(self, module_id: str) -> bool:
        """Remove a registered module."""
        return self._modules.pop(module_id, None) is not None

    def get(self, module_id: str) -> ModuleContract | None:
        """Return a module by ID, or None if it is not registered."""
        return self._modules.get(module_id)

    def has(self, module_id: str) -> bool:
        """Return whether a module is registered."""
        return module_id in self._modules

    def manifests(self) -> list[ModuleManifest]:
        """Return manifests for all registered modules."""
        return [module.manifest for module in self._modules.values()]

    def modules(self) -> list[ModuleContract]:
        """Return all registered module instances."""
        return list(self._modules.values())

    def ids(self) -> list[str]:
        """Return registered module IDs."""
        return list(self._modules.keys())

    def __iter__(self) -> Iterator[ModuleContract]:
        return iter(self._modules.values())

    def __len__(self) -> int:
        return len(self._modules)
