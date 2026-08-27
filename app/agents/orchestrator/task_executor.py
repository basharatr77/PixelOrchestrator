class TaskExecutor:
    def __init__(self, transport_resolver=None):
        if transport_resolver is None:
            from app.core.transport_resolver import TransportResolver

            transport_resolver = TransportResolver

        self.transport_resolver = transport_resolver

    def resolve_transport(self, task):
        from app.core.module_contract import (
            Device,
            DeviceState,
            ModuleType,
        )

        mode = task.get("mode")

        if mode is None:
            action = task.get("action")

            if action == "safe_probe":
                mode = "ADB"
            elif action == "diagnostic_scan":
                mode = "FASTBOOT"

        mode = mode.upper() if mode else None

        if mode == "ADB":
            module_type = ModuleType.ADB
            device_state = DeviceState.ADB
        elif mode == "FASTBOOT":
            module_type = ModuleType.FASTBOOT
            device_state = DeviceState.FASTBOOT
        else:
            raise ValueError(
                f"Unsupported transport mode: {mode}"
            )

        serial = task["serial"]

        device = Device(
            device_id=f"{mode.lower()}:{serial}",
            module_type=module_type,
            state=device_state,
            serial=serial,
            transport=mode.lower(),
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
