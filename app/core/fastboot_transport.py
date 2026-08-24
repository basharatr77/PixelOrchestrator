import subprocess

from app.core.transport import Transport


class FastbootTransport(Transport):
    def __init__(self, serial):
        self.serial = serial

    def connect(self):
        result = subprocess.run(
            ["fastboot", "-s", self.serial, "getvar", "product"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        output = (result.stdout + result.stderr).strip()

        return result.returncode == 0 and bool(output)

    def disconnect(self):
        return True

    def is_connected(self):
        return self.connect()

    def execute(self, command):
        result = subprocess.run(
            [
                "fastboot",
                "-s",
                self.serial,
                *command,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def get_device_info(self):
        result = subprocess.run(
            [
                "fastboot",
                "-s",
                self.serial,
                "getvar",
                "product",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        output = result.stdout + result.stderr

        product = ""

        for line in output.splitlines():
            line = line.strip()

            if "product:" in line:
                product = line.split("product:", 1)[1].strip()
                break

        return {
            "serial": self.serial,
            "product": product,
            "mode": "FASTBOOT",
        }
