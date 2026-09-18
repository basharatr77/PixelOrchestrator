from app.core.device_registry import DeviceRegistry
from app.core.module_contract import DeviceState


class DeviceAllocator:
    """Deterministically select an eligible registered device."""

    def __init__(self, registry: DeviceRegistry) -> None:
        if not isinstance(registry, DeviceRegistry):
            raise TypeError("registry must be a DeviceRegistry")

        self.registry = registry

    def select(self) -> str:
        """Return the device_id of the first eligible device.

        Eligible devices are currently those in ADB state.
        Selection is deterministic by device_id.
        """
        eligible = sorted(
            device_id
            for device_id, device in self.registry.snapshot().items()
            if device.state is DeviceState.ADB
        )

        if not eligible:
            raise RuntimeError("No eligible device")

        return eligible[0]
