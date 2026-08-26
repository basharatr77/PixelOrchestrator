"""Common module for PixelOrchestrator.

Provides vendor-neutral capabilities and actions that can be
shared by the GUI and vendor-specific modules.
"""

from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    Device,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)


class CommonModule(ModuleContract):
    """Vendor-neutral base module."""

    manifest = ModuleManifest(
        id="common",
        name="Common",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        description="Common device and orchestration functionality.",
        capabilities=(
            Capability(
                id="device_detection",
                name="Device Detection",
                description="Detect connected Android devices.",
            ),
            Capability(
                id="device_information",
                name="Device Information",
                description="Read generic device information.",
            ),
        ),
        actions=(
            Action(
                id="refresh_devices",
                name="Refresh Devices",
                description="Refresh the connected device list.",
                capability_id="device_detection",
                requires_device=False,
            ),
            Action(
                id="device_info",
                name="Device Information",
                description="Display generic device information.",
                capability_id="device_information",
                requires_device=True,
            ),
        ),
    )

    def detect(self) -> list[Device]:
        """Common module does not perform vendor-specific detection."""
        return []

    def execute(
        self,
        action_id: str,
        device: Device | None = None,
        **kwargs,
    ) -> ActionResult:
        """Execute a common action."""

        if action_id == "refresh_devices":
            return ActionResult(
                success=True,
                message="Device refresh requested.",
            )

        if action_id == "device_info":
            if device is None:
                return ActionResult(
                    success=False,
                    message="A device is required.",
                    error_code="DEVICE_REQUIRED",
                )

            return ActionResult(
                success=True,
                message="Device information available.",
                data={
                    "device_id": device.device_id,
                    "module_type": device.module_type.value,
                    "state": device.state.value,
                    "model": device.model,
                    "serial": device.serial,
                    "transport": device.transport,
                },
            )

        return ActionResult(
            success=False,
            message=f"Unknown action: {action_id}",
            error_code="UNKNOWN_ACTION",
        )
