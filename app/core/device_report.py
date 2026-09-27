"""Canonical device report builder."""

import json
from pathlib import Path

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


def export_device_report(device: Device, output_path: str | Path) -> Path:
    """Export a canonical device report as JSON."""
    path = Path(output_path)
    path.write_text(
        json.dumps(build_device_report(device), indent=2),
        encoding="utf-8",
    )
    return path
