from app.core.task import Task, TaskStatus


def test_running_task_can_be_rehydrated_as_pending_for_restart_recovery():
    task = Task(
        device_id="device:recovery-001",
        module_id="adb",
        action_id="probe",
        parameters={"mode": "safe"},
        id="task:recovery-001",
        status=TaskStatus.RUNNING,
        attempts=2,
        started_at=123.0,
    )

    recovered = Task(
        device_id=task.device_id,
        module_id=task.module_id,
        action_id=task.action_id,
        parameters=task.parameters,
        id=task.id,
        status=TaskStatus.PENDING,
        attempts=task.attempts,
        created_at=task.created_at,
        started_at=None,
        completed_at=None,
    )

    assert recovered.id == task.id
    assert recovered.status is TaskStatus.PENDING
    assert recovered.attempts == 2
    assert recovered.device_id == task.device_id
    assert recovered.module_id == task.module_id
    assert recovered.action_id == task.action_id
    assert recovered.parameters == task.parameters
