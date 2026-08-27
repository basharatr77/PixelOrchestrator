import subprocess

from app.core.module_contract import (
    Device,
    DeviceState,
    ModuleType,
)


def getprop(serial, prop):
    try:
        result = subprocess.check_output(
            [
                "adb",
                "-s",
                serial,
                "shell",
                "getprop",
                prop,
            ],
            text=True,
            timeout=5,
        )

        return result.strip()

    except Exception:
        return ""


def scan_adb():
    devices = []

    try:
        result = subprocess.check_output(
            ["adb", "devices"],
            text=True,
            timeout=5,
        )

        for line in result.splitlines()[1:]:
            if "\tdevice" not in line:
                continue

            serial = line.split()[0]

            brand = getprop(
                serial,
                "ro.product.manufacturer",
            )

            model = getprop(
                serial,
                "ro.product.model",
            )

            android_version = getprop(
                serial,
                "ro.build.version.release",
            )

            devices.append(
                Device(
                    device_id=f"adb:{serial}",
                    module_type=ModuleType.ADB,
                    state=DeviceState.ADB,
                    serial=serial,
                    transport="adb",
                    model=model,
                    properties={
                        "brand": brand,
                        "android_version": android_version,
                    },
                )
            )

    except Exception as e:
        print("ADB Error:", e)

    return devices
