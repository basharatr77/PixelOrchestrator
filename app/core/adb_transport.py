import subprocess

from app.core.transport import Transport


class ADBTransport(Transport):
    def __init__(self, serial):
        self.serial = serial

    def connect(self):
        result = subprocess.run(
            ["adb", "-s", self.serial, "get-state"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        return result.returncode == 0 and result.stdout.strip() == "device"

    def disconnect(self):
        return True

    def is_connected(self):
        return self.connect()

    def execute(self, command):
        result = subprocess.run(
            ["adb", "-s", self.serial, "shell", command],
            capture_output=True,
            text=True,
            timeout=10,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def get_device_info(self):
        def getprop(prop):
            result = subprocess.run(
                [
                    "adb",
                    "-s",
                    self.serial,
                    "shell",
                    "getprop",
                    prop,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return result.stdout.strip()

        return {
            "serial": self.serial,
            "brand": getprop("ro.product.manufacturer"),
            "model": getprop("ro.product.model"),
            "android_version": getprop("ro.build.version.release"),
        }
