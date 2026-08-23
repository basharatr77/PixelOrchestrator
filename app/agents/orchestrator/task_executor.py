class TaskExecutor:
    def execute(self, task):
        action = task.get("action")
        serial = task.get("serial")

        if action in {"safe_probe", "diagnostic_scan"}:
            return {
                "success": True,
                "action": action,
                "serial": serial,
            }

        if action == "ignore":
            return {
                "success": True,
                "action": "ignore",
                "serial": serial,
            }

        return {
            "success": False,
            "action": action,
            "serial": serial,
            "error": "unsupported_action",
        }
