"""Canonical device report builder."""

from app.core.module_contract import Device


def build_device_report(device: Device) -> dict:
    """Build a serializable report from a canonical Device."""
    if not isinstance(device, Device):
        raise TypeError("device must be a canonical Device.")

    return {
        "device_id": device.device_id,
        "module_type": device.module_type.value,
        "state": device.state.value,
        "model": device.model,
        "serial": device.serial,
        "transport": device.transport,
        "properties": dict(device.properties),
        "capabilities": list(device.capabilities or ()),
    }
