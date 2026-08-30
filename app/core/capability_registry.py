"""Capability Registry V1 for PixelOrchestrator.

Provides a central registry for canonical capability definitions.
The registry is intentionally independent from device detection,
transport implementations, GUI logic, and vendor-specific modules.
"""

from app.core.module_contract import Capability


class CapabilityRegistry:
    """Central registry for PixelOrchestrator capabilities."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        """Register a capability using its canonical ID."""

        if not isinstance(capability, Capability):
            raise TypeError("Capability must be a Capability instance.")

        capability_id = capability.id

        if not capability_id or not capability_id.strip():
            raise ValueError("Capability ID cannot be empty.")

        if capability_id in self._capabilities:
            raise ValueError(
                f"Capability '{capability_id}' is already registered."
            )

        self._capabilities[capability_id] = capability

    def unregister(self, capability_id: str) -> bool:
        """Remove a capability and report whether it existed."""

        return self._capabilities.pop(capability_id, None) is not None

    def get(self, capability_id: str) -> Capability | None:
        """Return a capability by ID, or None if absent."""

        return self._capabilities.get(capability_id)

    def has(self, capability_id: str) -> bool:
        """Return whether a capability is registered."""

        return capability_id in self._capabilities

    def all(self) -> list[Capability]:
        """Return all registered capabilities."""

        return list(self._capabilities.values())

    def ids(self) -> list[str]:
        """Return all registered capability IDs."""

        return list(self._capabilities.keys())

    def clear(self) -> None:
        """Remove all registered capabilities."""

        self._capabilities.clear()

    def __len__(self) -> int:
        return len(self._capabilities)
