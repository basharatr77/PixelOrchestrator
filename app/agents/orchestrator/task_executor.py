from app.agents.device_agent.device_model import Device


class TaskExecutor:
    def __init__(self, transport_resolver=None):
        if transport_resolver is None:
            from app.core.transport_resolver import TransportResolver

            transport_resolver = TransportResolver

        self.transport_resolver = transport_resolver

    def resolve_transport(self, task):
        device = Device(
            serial=task["serial"],
            mode=task["mode"],
        )

        return self.transport_resolver.resolve(device)

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
