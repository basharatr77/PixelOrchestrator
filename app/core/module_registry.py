"""Module Registry v1 for PixelOrchestrator.

The registry provides a central, vendor-neutral catalog of modules.
It does not contain vendor-specific implementation logic.
"""

from typing import Iterator

from app.core.capability_registry import CapabilityRegistry
from app.core.module_contract import ModuleContract, ModuleManifest


class ModuleRegistry:
    """Central registry for PixelOrchestrator modules."""

    def __init__(
        self,
        capability_registry: CapabilityRegistry | None = None,
    ) -> None:
        self._modules: dict[str, ModuleContract] = {}
        self._capability_owners: dict[str, set[str]] = {}
        self.capability_registry = (
            capability_registry
            if capability_registry is not None
            else CapabilityRegistry()
        )

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

        registered_capabilities = []

        try:
            for capability in module.get_capabilities():
                if not self.capability_registry.has(capability.id):
                    self.capability_registry.register(capability)
                    registered_capabilities.append(capability.id)

                self._capability_owners.setdefault(
                    capability.id,
                    set(),
                ).add(module_id)

            self._modules[module_id] = module

        except Exception:
            for capability in module.get_capabilities():
                owners = self._capability_owners.get(capability.id)

                if owners is not None:
                    owners.discard(module_id)

                    if not owners:
                        self._capability_owners.pop(
                            capability.id,
                            None,
                        )

            for capability_id in registered_capabilities:
                self.capability_registry.unregister(capability_id)

            raise

    def unregister(self, module_id: str) -> bool:
        """Remove a registered module and clean up orphaned capabilities."""

        module = self._modules.pop(module_id, None)

        if module is None:
            return False

        for capability in module.get_capabilities():
            owners = self._capability_owners.get(capability.id)

            if owners is None:
                continue

            owners.discard(module_id)

            if not owners:
                self._capability_owners.pop(capability.id, None)
                self.capability_registry.unregister(capability.id)

        return True

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

    def get_capabilities(self):
        """Return all capabilities exposed by registered modules."""

        capabilities = []

        for module in self._modules.values():
            capabilities.extend(module.get_capabilities())

        return capabilities

    def ids(self) -> list[str]:
        """Return registered module IDs."""
        return list(self._modules.keys())

    def __iter__(self) -> Iterator[ModuleContract]:
        return iter(self._modules.values())

    def __len__(self) -> int:
        return len(self._modules)
