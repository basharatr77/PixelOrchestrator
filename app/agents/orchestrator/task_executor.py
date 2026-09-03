"""Task execution layer for PixelOrchestrator."""

from app.core.device_registry import DeviceRegistry
from app.core.module_registry import ModuleRegistry
from app.core.task import Task
from app.core.retry_policy import RetryPolicy


class TaskExecutor:
    """Execute canonical Tasks while preserving the legacy task path."""

    def __init__(
        self,
        transport_resolver=None,
        module_registry=None,
        device_registry=None,
        retry_policy=None,
    ):
        if transport_resolver is None:
            from app.core.transport_resolver import TransportResolver

            transport_resolver = TransportResolver

        self.transport_resolver = transport_resolver
        self.module_registry = (
            module_registry
            if module_registry is not None
            else ModuleRegistry()
        )
        self.device_registry = (
            device_registry
            if device_registry is not None
            else DeviceRegistry()
        )
        self.retry_policy = (
            retry_policy
            if retry_policy is not None
            else RetryPolicy()
        )

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

    def _execute_canonical(self, task):
        from app.core.module_contract import ActionResult

        module = self.module_registry.get(task.module_id)

        if module is None:
            task.start()
            result = ActionResult(
                success=False,
                message=f"Module '{task.module_id}' was not found.",
                error_code="MODULE_NOT_FOUND",
            )
            task.fail(result)
            return result

        action = next(
            (
                item
                for item in module.get_actions()
                if item.id == task.action_id
            ),
            None,
        )

        if action is None:
            task.start()
            result = ActionResult(
                success=False,
                message=(
                    f"Action '{task.action_id}' was not found "
                    f"in module '{task.module_id}'."
                ),
                error_code="ACTION_NOT_FOUND",
            )
            task.fail(result)
            return result

        device = None

        if action.requires_device:
            device = self.device_registry.get(task.device_id)

            if device is None:
                task.start()
                result = ActionResult(
                    success=False,
                    message=f"Device '{task.device_id}' was not found.",
                    error_code="DEVICE_NOT_FOUND",
                )
                task.fail(result)
                return result

        while True:
            task.start()

            try:
                result = module.execute(
                    task.action_id,
                    device=device,
                    **task.parameters,
                )

                if not isinstance(result, ActionResult):
                    result = ActionResult(
                        success=False,
                        message="Module returned an invalid action result.",
                        error_code="INVALID_ACTION_RESULT",
                    )

            except Exception as exc:
                result = ActionResult(
                    success=False,
                    message=f"Task execution failed: {exc}",
                    error_code="EXECUTION_ERROR",
                )

            if result.success:
                task.complete(result)
                return result

            if self.retry_policy.should_retry(task.attempts, result):
                task.retry(result)
                continue

            task.fail(result)
            return result

    def execute(self, task):
        if isinstance(task, Task):
            return self._execute_canonical(task)

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
