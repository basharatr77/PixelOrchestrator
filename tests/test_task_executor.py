from app.agents.orchestrator.task_executor import TaskExecutor


class FakeTransport:
    def execute(self, command):
        assert command == "getprop ro.product.model"

        return {
            "returncode": 0,
            "stdout": "Pixel 8\n",
            "stderr": "",
        }


class FakeTransportResolver:
    @staticmethod
    def resolve(device):
        assert device.serial == "PIXEL_8"
        assert device.state.value.upper() == "ADB"

        return FakeTransport()


def test_safe_probe_executes_read_only_probe():
    executor = TaskExecutor(
        transport_resolver=FakeTransportResolver,
    )

    result = executor.execute({
        "action": "safe_probe",
        "serial": "PIXEL_8",
        "mode": "ADB",
    })

    assert result == {
        "success": True,
        "action": "safe_probe",
        "serial": "PIXEL_8",
        "returncode": 0,
        "stdout": "Pixel 8\n",
        "stderr": "",
    }


def test_diagnostic_scan_is_executed_as_dry_run():
    executor = TaskExecutor()

    result = executor.execute({
        "action": "diagnostic_scan",
        "serial": "PIXEL_8",
    })

    assert result == {
        "success": True,
        "action": "diagnostic_scan",
        "serial": "PIXEL_8",
    }


def test_ignore_task_does_not_execute_device_operation():
    executor = TaskExecutor()

    result = executor.execute({
        "action": "ignore",
        "serial": "PIXEL_8",
    })

    assert result == {
        "success": True,
        "action": "ignore",
        "serial": "PIXEL_8",
    }


def test_unknown_action_returns_controlled_failure():
    executor = TaskExecutor()

    result = executor.execute({
        "action": "unknown_action",
        "serial": "PIXEL_8",
    })

    assert result == {
        "success": False,
        "action": "unknown_action",
        "serial": "PIXEL_8",
        "error": "unsupported_action",
    }
