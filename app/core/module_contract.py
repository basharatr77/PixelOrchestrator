"""Module Contract v1 for PixelOrchestrator.

This file defines the stable interface shared by all modules.
GUI and ModuleRegistry should depend on this contract rather than
vendor-specific implementations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModuleType(str, Enum):
    COMMON = "common"
    ADB = "adb"
    FASTBOOT = "fastboot"
    MEDIATEK = "mediatek"
    QUALCOMM = "qualcomm"
    UNISOC = "unisoc"
    SAMSUNG = "samsung"


class DeviceState(str, Enum):
    UNKNOWN = "unknown"
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ADB = "adb"
    FASTBOOT = "fastboot"
    FASTBOOTD = "fastbootd"
    RECOVERY = "recovery"
    SIDELOAD = "sideload"
    BROM = "brom"
    EDL = "edl"
    PRELOADER = "preloader"
    DOWNLOAD = "download"


@dataclass(frozen=True)
class Capability:
    """A capability exposed by a module."""

    id: str
    name: str
    description: str = ""
    enabled: bool = True


@dataclass(frozen=True)
class Action:
    """An action that a module can expose to the GUI/orchestrator."""

    id: str
    name: str
    description: str = ""
    capability_id: str | None = None
    requires_device: bool = True
    dangerous: bool = False
    enabled: bool = True


@dataclass
class Device:
    """Generic device representation shared across modules."""

    device_id: str
    module_type: ModuleType
    state: DeviceState = DeviceState.UNKNOWN
    model: str | None = None
    serial: str | None = None
    transport: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    """Standard result returned by module actions."""

    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None


@dataclass(frozen=True)
class ModuleManifest:
    """Metadata used by the registry and dynamic GUI."""

    id: str
    name: str
    version: str
    module_type: ModuleType
    description: str = ""
    capabilities: tuple[Capability, ...] = ()
    actions: tuple[Action, ...] = ()


class ModuleContract:
    """Base contract every PixelOrchestrator module must follow."""

    manifest: ModuleManifest

    def validate_manifest(self) -> None:
        """Validate the structural integrity of the module manifest."""

        manifest = self.manifest

        if not manifest.id or not manifest.id.strip():
            raise ValueError("Module manifest ID cannot be empty.")

        if not manifest.name or not manifest.name.strip():
            raise ValueError("Module manifest name cannot be empty.")

        if not manifest.version or not manifest.version.strip():
            raise ValueError("Module manifest version cannot be empty.")

        capability_ids = set()

        for capability in manifest.capabilities:
            if not capability.id or not capability.id.strip():
                raise ValueError("Capability ID cannot be empty.")

            if capability.id in capability_ids:
                raise ValueError(
                    f"Duplicate capability ID: {capability.id}"
                )

            capability_ids.add(capability.id)

        action_ids = set()

        for action in manifest.actions:
            if not action.id or not action.id.strip():
                raise ValueError("Action ID cannot be empty.")

            if action.id in action_ids:
                raise ValueError(
                    f"Duplicate action ID: {action.id}"
                )

            action_ids.add(action.id)

            if (
                action.capability_id is not None
                and not action.capability_id.strip()
            ):
                raise ValueError(
                    "Action capability ID cannot be empty when provided."
                )

            if (
                action.capability_id is not None
                and action.capability_id not in capability_ids
            ):
                raise ValueError(
                    f"Unknown capability ID: {action.capability_id}"
                )

    def detect(self) -> list[Device]:
        """Detect devices supported by this module."""
        raise NotImplementedError

    def get_capabilities(self) -> list[Capability]:
        """Return capabilities exposed by this module."""
        return list(self.manifest.capabilities)

    def get_actions(self) -> list[Action]:
        """Return actions exposed by this module."""
        return list(self.manifest.actions)

    def execute(
        self,
        action_id: str,
        device: Device | None = None,
        **kwargs: Any,
    ) -> ActionResult:
        """Execute a module action."""
        raise NotImplementedError
