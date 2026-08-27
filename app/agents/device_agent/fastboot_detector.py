import subprocess

from app.core.module_contract import (
    Device,
    DeviceState,
    ModuleType,
)


def scan_fastboot():
    devices = []

    try:
        result = subprocess.check_output(
            ["fastboot", "devices"],
            text=True,
        )

        for line in result.splitlines():
            if not line.strip():
                continue

            serial = line.split()[0]

            devices.append(
                Device(
                    device_id=f"fastboot:{serial}",
                    module_type=ModuleType.FASTBOOT,
                    state=DeviceState.FASTBOOT,
                    serial=serial,
                    transport="fastboot",
                )
            )

    except Exception as e:
        print("Fastboot Error:", e)

    return devices
