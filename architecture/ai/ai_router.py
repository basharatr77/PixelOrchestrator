class AIRouter:
    def decide(self, event):
        if event["type"] == "DEVICE_DETECTED":
            return "START_ANALYSIS"
        return "IGNORE"
