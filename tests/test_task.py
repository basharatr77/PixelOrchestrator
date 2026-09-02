from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus


def test_task_defaults_are_valid():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )

    assert task.id
    assert task.status is TaskStatus.PENDING
    assert task.attempts == 0
    assert task.result is None
    assert task.created_at > 0
    assert task.started_at is None
    assert task.completed_at is None
    assert task.parameters == {}


def test_task_parameters_are_defensively_copied():
    parameters = {"command": "getprop"}

    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
        parameters=parameters,
    )

    parameters["command"] = "dangerous-change"

    assert task.parameters["command"] == "getprop"


def test_task_rejects_empty_identity_fields():
    for field, kwargs in (
        ("device_id", {"device_id": " "}),
        ("module_id", {"module_id": ""}),
        ("action_id", {"action_id": " "}),
    ):
        base = {
            "device_id": "device-1",
            "module_id": "adb",
            "action_id": "shell",
        }
        base.update(kwargs)

        try:
            Task(**base)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{field} should reject empty value")


def test_task_rejects_non_dict_parameters():
    try:
        Task(
            device_id="device-1",
            module_id="adb",
            action_id="shell",
            parameters=[],
        )
    except TypeError:
        pass
    else:
        raise AssertionError("Task should reject non-dict parameters")


def test_task_starts_and_increments_attempts():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )

    task.start()

    assert task.status is TaskStatus.RUNNING
    assert task.attempts == 1
    assert task.started_at is not None


def test_task_completes_with_action_result():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )
    result = ActionResult(success=True, message="ok")

    task.start()
    task.complete(result)

    assert task.status is TaskStatus.COMPLETED
    assert task.result is result
    assert task.completed_at is not None


def test_task_fails_with_action_result():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )
    result = ActionResult(
        success=False,
        message="failed",
        error_code="TEST_FAILURE",
    )

    task.start()
    task.fail(result)

    assert task.status is TaskStatus.FAILED
    assert task.result is result
    assert task.completed_at is not None


def test_pending_task_can_be_cancelled():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )

    task.cancel()

    assert task.status is TaskStatus.CANCELLED
    assert task.completed_at is not None


def test_running_task_can_be_cancelled():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )

    task.start()
    task.cancel()

    assert task.status is TaskStatus.CANCELLED
    assert task.completed_at is not None


def test_completed_task_cannot_be_started_again():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )

    task.start()
    task.complete(ActionResult(success=True))

    try:
        task.start()
    except ValueError:
        pass
    else:
        raise AssertionError("Completed task must not restart")


def test_completed_task_cannot_be_cancelled():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )

    task.start()
    task.complete(ActionResult(success=True))

    try:
        task.cancel()
    except ValueError:
        pass
    else:
        raise AssertionError("Completed task must not be cancelled")


def test_task_requires_action_result_for_completion():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )

    task.start()

    try:
        task.complete({"success": True})
    except TypeError:
        pass
    else:
        raise AssertionError("Task must require ActionResult")


def test_task_requires_action_result_for_failure():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
    )

    task.start()

    try:
        task.fail({"success": False})
    except TypeError:
        pass
    else:
        raise AssertionError("Task must require ActionResult")


def test_task_status_accepts_valid_string_value():
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="shell",
        status="pending",
    )

    assert task.status is TaskStatus.PENDING
