def decide(device):
    """
    Simple AI rule-based brain (upgrade later to LLM)
    """

    decision = {
        "serial": device.get("serial"),
        "action": "ignore",
        "confidence": 0.5
    }

    mode = device.get("mode")

    if mode == "FASTBOOT":
        decision["action"] = "diagnostic_scan"
        decision["confidence"] = 0.8

    elif mode == "ADB":
        decision["action"] = "safe_probe"
        decision["confidence"] = 0.9

    if len(device.get("serial","")) > 12:
        decision["action"] = "deep_analyze"
        decision["confidence"] = 0.95

    return decision
