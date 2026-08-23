import subprocess

from app.agents.device_agent.device_model import Device


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

            devices.append(
                Device(
                    serial=serial,
                    mode="ADB",
                    brand=getprop(
                        serial,
                        "ro.product.manufacturer",
                    ),
                    model=getprop(
                        serial,
                        "ro.product.model",
                    ),
                    android_version=getprop(
                        serial,
                        "ro.build.version.release",
                    ),
                )
            )

    except Exception as e:
        print("ADB Error:", e)

    return devices
