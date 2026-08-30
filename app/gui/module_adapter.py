"""GUI Module Adapter V1 for PixelOrchestrator.

Converts registered module metadata into GUI-friendly structures.
The GUI does not need vendor-specific knowledge.
"""

from app.core.module_contract import Action, ActionResult, Capability
from app.core.module_loader import ModuleLoader
from app.core.module_registry import ModuleRegistry


class GUIModuleAdapter:
    """Expose registered module metadata to the GUI."""

    def __init__(
        self,
        registry: ModuleRegistry | None = None,
    ) -> None:
        self.loader = ModuleLoader(registry)
        self.registry = self.loader.registry

    def load_modules(self) -> None:
        """Load available built-in modules."""
        self.loader.load_builtin_modules()

    def get_modules(self) -> list[dict]:
        """Return GUI-friendly module information."""

        result = []

        for module in self.registry.modules():
            result.append(
                {
                    "id": module.manifest.id,
                    "name": module.manifest.name,
                    "version": module.manifest.version,
                    "type": module.manifest.module_type.value,
                    "description": module.manifest.description,
                }
            )

        return result

    def get_capabilities(self, module_id: str) -> list[Capability]:
        """Return capabilities exposed by a module."""

        module = self.registry.get(module_id)

        if module is None:
            return []

        return module.get_capabilities()

    def get_actions(self, module_id: str) -> list[Action]:
        """Return actions exposed by a module."""

        module = self.registry.get(module_id)

        if module is None:
            return []

        return module.get_actions()

    def get_action_buttons(self, module_id: str) -> list[dict]:
        """Return action metadata suitable for GUI buttons."""

        actions = self.get_actions(module_id)

        return [
            {
                "id": action.id,
                "name": action.name,
                "description": action.description,
                "capability_id": action.capability_id,
                "requires_device": action.requires_device,
                "dangerous": action.dangerous,
                "enabled": action.enabled,
            }
            for action in actions
        ]

    def execute_action(
        self,
        module_id: str,
        action_id: str,
        device=None,
        **kwargs,
    ) -> ActionResult:
        """Execute an action through the registered module."""

        module = self.registry.get(module_id)

        if module is None:
            return ActionResult(
                success=False,
                message=f"Module not found: {module_id}",
                error_code="MODULE_NOT_FOUND",
            )

        return module.execute(
            action_id,
            device=device,
            **kwargs,
        )
