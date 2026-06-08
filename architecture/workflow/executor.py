class Executor:
    def execute(self, decision, data):
        if decision == "START_ANALYSIS":
            return self.analyze_device(data)
        return "NO_ACTION"

    def analyze_device(self, data):
        return {
            "status": "ANALYZED",
            "device": data["id"]
        }
