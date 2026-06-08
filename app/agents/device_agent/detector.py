import time
import subprocess

def run(cmd):
    try:
        return subprocess.check_output(cmd, text=True)
    except:
        return ""

def scan_adb():
    out = run(["adb", "devices"])
    return [
        {"serial": l.split()[0], "mode": "ADB"}
        for l in out.splitlines()[1:]
        if "\tdevice" in l
    ]

def scan_fastboot():
    out = run(["fastboot", "devices"])
    return [
        {"serial": l.split()[0], "mode": "FASTBOOT"}
        for l in out.splitlines()
        if l.strip()
    ]

def start_detector():
    print("🚀 Device Discovery Service Started")

    known = set()

    while True:
        devices = scan_adb() + scan_fastboot()
        current = set(d["serial"] for d in devices)

        for d in devices:
            if d["serial"] not in known:
                print("🟢 CONNECTED:", d)

        for d in known - current:
            print("🔴 DISCONNECTED:", d)

        known = current
        time.sleep(3)

if __name__ == "__main__":
    start_detector()
