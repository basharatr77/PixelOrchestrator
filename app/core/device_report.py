"""Canonical device report builder."""

import json
from pathlib import Path

from app.core.module_contract import Device


def export_device_report_pdf(device: Device, output_path: str | Path) -> Path:
    """Export a canonical device report as a PDF using Qt."""
    import app.gui.qt_bootstrap
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QFont, QGuiApplication, QPainter, QPdfWriter

    path = Path(output_path)
    report = build_device_report(device)
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([])

    writer = QPdfWriter(str(path))
    writer.setTitle("PixelOrchestrator Device Report")
    writer.setCreator("PixelOrchestrator")

    painter = QPainter(writer)
    try:
        painter.setFont(QFont("Arial", 11))
        rect = QRectF(60, 60, writer.width() - 120, writer.height() - 120)
        lines = [
            "PixelOrchestrator Device Report",
            "",
            f"Device ID: {report['device_id']}",
            f"Module Type: {report['module_type']}",
            f"State: {report['state']}",
            f"Model: {report['model']}",
            f"Serial: {report['serial']}",
            f"Transport: {report['transport']}",
            f"Properties: {report['properties']}",
            f"Capabilities: {report['capabilities']}",
        ]
        painter.drawText(rect, "\n".join(lines))
    finally:
        painter.end()

    return path



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
