import time

from app.agents.device_agent.adb_detector import scan_adb
from app.agents.device_agent.fastboot_detector import scan_fastboot
from app.core.events import Event


def _device_brand(device):
    """Return device brand when available."""
    properties = getattr(device, "properties", None)
    if isinstance(properties, dict):
        return properties.get("brand", "")
    return getattr(device, "brand", "") or ""


def _device_android_version(device):
    """Return Android version when available."""
    properties = getattr(device, "properties", None)
    if isinstance(properties, dict):
        return properties.get("android_version", "")
    return getattr(device, "android_version", "") or ""


def _device_mode(device):
    """Return the lifecycle-compatible uppercase device state."""
    return device.state.value.upper()


def scan_devices():
    return scan_adb() + scan_fastboot()


def detect_lifecycle(known_devices, devices=None):
    if devices is None:
        devices = scan_devices()

    current_devices = {
        device.serial: device
        for device in devices
    }

    events = []

    # Support both:
    #   legacy: set({"PIXEL_8"})
    #   current: {"PIXEL_8": "ADB"}
    legacy_serials = isinstance(known_devices, set)

    if legacy_serials:
        known_serials = known_devices
    else:
        known_serials = set(known_devices)

    # New devices and mode transitions
    for serial, device in current_devices.items():
        if serial not in known_serials:
            events.append({
                "type": "DEVICE_CONNECTED",
                "data": {
                    "serial": device.serial,
                    "mode": _device_mode(device),
                    "brand": _device_brand(device),
                    "model": device.model or "",
                    "android_version": _device_android_version(device),
                },
            })
            continue

        # Mode transitions require the newer serial -> mode mapping.
        if not legacy_serials:
            previous_mode = known_devices[serial]

            if previous_mode != _device_mode(device):
                events.append({
                    "type": "DEVICE_MODE_CHANGED",
                    "data": {
                        "serial": serial,
                        "previous_mode": previous_mode,
                        "mode": _device_mode(device),
                    },
                })

    # Disconnected devices
    for serial in known_serials:
        if serial not in current_devices:
            events.append({
                "type": "DEVICE_DISCONNECTED",
                "data": {
                    "serial": serial,
                },
            })

    return events


async def publish_lifecycle_events(bus, lifecycle_events):
    for lifecycle in lifecycle_events:
        event = Event(
            lifecycle["type"],
            lifecycle["data"],
        )
        await bus.publish(event)


async def run_detector_cycle(bus, known_devices):
    devices = scan_devices()

    lifecycle_events = detect_lifecycle(
        known_devices,
        devices,
    )

    await publish_lifecycle_events(
        bus,
        lifecycle_events,
    )

    return {
        device.serial: _device_mode(device)
        for device in devices
    }

def start_detector():
    print("Device Discovery Service Started")

    known = {}

    while True:
        devices = scan_devices()
        current = {
            device.serial: _device_mode(device)
            for device in devices
        }

        for device in devices:
            if device.serial not in known:
                print(
                    "CONNECTED:",
                    {
                        "serial": device.serial,
                        "mode": _device_mode(device),
                        "brand": _device_brand(device),
                        "model": device.model or "",
                        "android_version": _device_android_version(device),
                    },
                )
            elif known[device.serial] != _device_mode(device):
                print(
                    "MODE CHANGED:",
                    device.serial,
                    known[device.serial],
                    "->",
                    _device_mode(device),
                )

        for serial in known:
            if serial not in current:
                print("DISCONNECTED:", serial)

        known = current
        time.sleep(3)


if __name__ == "__main__":
    start_detector()
