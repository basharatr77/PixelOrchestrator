from app.agents.orchestrator.task_executor import TaskExecutor


def test_safe_probe_is_executed_as_dry_run():
    executor = TaskExecutor()

    result = executor.execute({
        "action": "safe_probe",
        "serial": "PIXEL_8",
    })

    assert result == {
        "success": True,
        "action": "safe_probe",
        "serial": "PIXEL_8",
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
