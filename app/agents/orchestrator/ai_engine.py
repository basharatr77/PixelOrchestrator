def decide(device):
    mode = device.get("mode")

    if mode == "ADB":
        return {"action": "safe_probe", "serial": device["serial"]}

    if mode == "FASTBOOT":
        return {"action": "diagnostic_scan", "serial": device["serial"]}

    return {"action": "ignore", "serial": device["serial"]}
