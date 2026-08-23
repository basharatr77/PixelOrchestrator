import time

from app.agents.device_agent.adb_detector import scan_adb
from app.agents.device_agent.fastboot_detector import scan_fastboot


def scan_devices():
    return scan_adb() + scan_fastboot()


def detect_lifecycle(known_devices):
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
                "data": device.to_dict(),
            })
            continue

        # Mode transitions require the newer serial -> mode mapping.
        if not legacy_serials:
            previous_mode = known_devices[serial]

            if previous_mode != device.mode:
                events.append({
                    "type": "DEVICE_MODE_CHANGED",
                    "data": {
                        "serial": serial,
                        "previous_mode": previous_mode,
                        "mode": device.mode,
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

def start_detector():
    print("Device Discovery Service Started")

    known = {}

    while True:
        devices = scan_devices()
        current = {
            device.serial: device.mode
            for device in devices
        }

        for device in devices:
            if device.serial not in known:
                print("CONNECTED:", device.to_dict())
            elif known[device.serial] != device.mode:
                print(
                    "MODE CHANGED:",
                    device.serial,
                    known[device.serial],
                    "->",
                    device.mode,
                )

        for serial in known:
            if serial not in current:
                print("DISCONNECTED:", serial)

        known = current
        time.sleep(3)


if __name__ == "__main__":
    start_detector()
