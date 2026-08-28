"""Canonical in-memory device registry.

The DeviceRegistry stores canonical Device objects keyed by their
stable device_id. It is intentionally independent from persistence,
event-bus implementation details, and vendor-specific logic.
"""

from app.core.module_contract import Device


class DeviceRegistry:
    """Registry for canonical PixelOrchestrator devices."""

    def __init__(self) -> None:
        self._devices: dict[str, Device] = {}

    def register(self, device: Device) -> None:
        """Register a new device.

        Raises:
            TypeError: if the value is not a canonical Device.
            ValueError: if the device_id is already registered.
        """
        if not isinstance(device, Device):
            raise TypeError("Device must be a canonical Device.")

        device_id = device.device_id

        if device_id in self._devices:
            raise ValueError(
                f"Device '{device_id}' is already registered."
            )

        self._devices[device_id] = device

    def get(self, device_id: str) -> Device | None:
        """Return a device by device_id, or None if absent."""
        return self._devices.get(device_id)

    def contains(self, device_id: str) -> bool:
        """Return whether a device_id is registered."""
        return device_id in self._devices

    def update(self, device: Device) -> None:
        """Replace an existing registered device.

        Raises:
            TypeError: if the value is not a canonical Device.
            KeyError: if the device_id is not registered.
        """
        if not isinstance(device, Device):
            raise TypeError("Device must be a canonical Device.")

        device_id = device.device_id

        if device_id not in self._devices:
            raise KeyError(
                f"Device '{device_id}' is not registered."
            )

        self._devices[device_id] = device

    def remove(self, device_id: str) -> bool:
        """Remove a device and report whether it existed."""
        return self._devices.pop(device_id, None) is not None

    def snapshot(self) -> dict[str, Device]:
        """Return a shallow copy of the current registry."""
        return dict(self._devices)

    def clear(self) -> None:
        """Remove all registered devices."""
        self._devices.clear()

    def __len__(self) -> int:
        return len(self._devices)
