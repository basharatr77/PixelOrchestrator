import subprocess

def scan_fastboot():
    devices = []

    try:
        result = subprocess.check_output(
            ["fastboot", "devices"],
            text=True
        )

        for line in result.splitlines():
            if line.strip():
                serial = line.split()[0]

                devices.append({
                    "serial": serial,
                    "mode": "FASTBOOT"
                })

    except Exception as e:
        print("Fastboot Error:", e)

    return devices
