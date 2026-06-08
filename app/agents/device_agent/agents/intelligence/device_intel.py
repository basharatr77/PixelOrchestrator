def enrich_device(device):
    serial = device.get("serial", "")

    info = {
        "serial": serial,
        "brand": "unknown",
        "model": "unknown",
        "risk_level": "low",
        "capabilities": []
    }

    if device.get("mode") == "FASTBOOT":
        info["capabilities"].append("flash_possible")
        info["risk_level"] = "medium"

    if device.get("mode") == "ADB":
        info["capabilities"].append("debug_access")

    if len(serial) > 12:
        info["brand"] = "Android Device"
        info["model"] = "auto-detected"

    return info
