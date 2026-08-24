class TaskExecutor:
    def __init__(self, transport_resolver=None):
        if transport_resolver is None:
            from app.core.transport_resolver import TransportResolver

            transport_resolver = TransportResolver

        self.transport_resolver = transport_resolver

    def resolve_transport(self, task):
        from app.agents.device_agent.device_model import Device

        mode = task.get("mode")

        if mode is None:
            action = task.get("action")

            if action == "safe_probe":
                mode = "ADB"
            elif action == "diagnostic_scan":
                mode = "FASTBOOT"

        device = Device(
            serial=task["serial"],
            mode=mode,
        )

        return self.transport_resolver.resolve(device)

    def execute(self, task):
        action = task.get("action")
        serial = task.get("serial")

        if action == "safe_probe":
            transport = self.resolve_transport(task)

            result = transport.execute(
                "getprop ro.product.model"
            )

            return {
                "success": result["returncode"] == 0,
                "action": action,
                "serial": serial,
                "returncode": result["returncode"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
            }

        if action == "diagnostic_scan":
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
