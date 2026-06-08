import subprocess

def scan_adb():
    devices = []

    try:
        result = subprocess.check_output(
            ["adb", "devices"],
            text=True
        )

        for line in result.splitlines()[1:]:
            if "\tdevice" in line:
                serial = line.split()[0]

                devices.append({
                    "serial": serial,
                    "mode": "ADB"
                })

    except Exception as e:
        print("ADB Error:", e)

    return devices
