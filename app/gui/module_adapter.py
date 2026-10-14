"""GUI Module Adapter V1 for PixelOrchestrator.

Converts registered module metadata into GUI-friendly structures.
The GUI does not need vendor-specific knowledge.
"""

import secrets
import threading

from app.core.action_authorization import validate_action_authorization
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
        self._dangerous_action_approvals: dict[
            str, tuple[str, str, str | None]
        ] = {}
        self._dangerous_action_approval_lock = threading.Lock()

    def approve_dangerous_action(
        self,
        module_id: str,
        action_id: str,
        device=None,
    ) -> str:
        """Issue a one-time approval bound to an action and device."""
        device_id = getattr(device, "device_id", None)
        token = secrets.token_urlsafe(32)
        with self._dangerous_action_approval_lock:
            self._dangerous_action_approvals[token] = (
                module_id,
                action_id,
                device_id,
            )
        return token

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
                "allowed_transports": action.allowed_transports,
                "allowed_states": action.allowed_states,
            }
            for action in actions
        ]

    def execute_action(
        self,
        module_id: str,
        action_id: str,
        device=None,
        approval_token: str | None = None,
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

        action = next(
            (item for item in module.get_actions() if item.id == action_id),
            None,
        )

        if action is None:
            return ActionResult(
                success=False,
                message=f"Action not found: {action_id}",
                error_code="ACTION_NOT_FOUND",
            )

        if getattr(action, "dangerous", False):
            device_id = getattr(device, "device_id", None)
            expected_approval = (module_id, action_id, device_id)

            # Validate and consume the token atomically. A mismatched request
            # cannot steal an approval intended for another action or device.
            with self._dangerous_action_approval_lock:
                approved_request = (
                    self._dangerous_action_approvals.get(approval_token)
                    if approval_token is not None
                    else None
                )
                if approved_request != expected_approval:
                    return ActionResult(
                        success=False,
                        message=(
                            f"Dangerous action '{action_id}' requires "
                            "explicit approval for this exact execution "
                            "and device."
                        ),
                        error_code="DANGEROUS_ACTION_REQUIRES_APPROVAL",
                    )
                del self._dangerous_action_approvals[approval_token]

        rejection = validate_action_authorization(
            action,
            module.get_capabilities(),
            device,
        )

        if rejection is not None:
            return rejection

        return module.execute(
            action_id,
            device=device,
            **kwargs,
        )
