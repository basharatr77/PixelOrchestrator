import pytest

from app.core.task import Task, TaskStatus
from app.core.module_contract import ActionResult


def test_task_repository_persists_and_reloads_task(tmp_path):
    from app.core.task_repository import TaskRepository

    db_path = tmp_path / "tasks.db"
    repository = TaskRepository(db_path)

    task = Task(
        device_id="device:repo-001",
        module_id="adb",
        action_id="probe",
        parameters={"mode": "safe", "scope": "basic"},
        id="task:repo-001",
        attempts=2,
    )

    repository.save(task)

    fresh_repository = TaskRepository(db_path)
    loaded = fresh_repository.get("task:repo-001")

    assert loaded is not None
    assert loaded.id == task.id
    assert loaded.device_id == task.device_id
    assert loaded.module_id == task.module_id
    assert loaded.action_id == task.action_id
    assert loaded.parameters == task.parameters
    assert loaded.status is TaskStatus.PENDING
    assert loaded.attempts == 2


def test_task_repository_rejects_non_task(tmp_path):
    from app.core.task_repository import TaskRepository

    repository = TaskRepository(tmp_path / "tasks.db")

    with pytest.raises(TypeError, match="canonical Task"):
        repository.save(object())


def test_task_repository_rejects_duplicate_task_id(tmp_path):
    from app.core.task_repository import TaskRepository

    repository = TaskRepository(tmp_path / "tasks.db")

    task = Task(
        device_id="device:repo-002",
        module_id="adb",
        action_id="probe",
        id="task:repo-002",
    )

    repository.save(task)

    with pytest.raises(ValueError, match="already exists"):
        repository.save(task)

def test_task_repository_updates_existing_task_state(tmp_path):
    from app.core.task_repository import TaskRepository

    db_path = tmp_path / "tasks.db"
    repository = TaskRepository(db_path)

    task = Task(
        device_id="device:repo-update-001",
        module_id="adb",
        action_id="probe",
        id="task:repo-update-001",
    )
    repository.save(task)

    task.start()
    repository.update(task)

    fresh_repository = TaskRepository(db_path)
    loaded = fresh_repository.get("task:repo-update-001")

    assert loaded is not None
    assert loaded.status is TaskStatus.RUNNING
    assert loaded.attempts == 1
    assert loaded.started_at is not None

def test_task_repository_recovers_running_task_as_pending(tmp_path):
    from app.core.task_repository import TaskRepository

    db_path = tmp_path / "tasks.db"
    repository = TaskRepository(db_path)

    task = Task(
        device_id="device:recovery-002",
        module_id="adb",
        action_id="probe",
        parameters={"mode": "safe"},
        id="task:recovery-002",
    )
    repository.save(task)

    task.start()
    repository.update(task)

    recovered = repository.recover("task:recovery-002")

    assert recovered is not None
    assert recovered.id == task.id
    assert recovered.status is TaskStatus.PENDING
    assert recovered.attempts == 1
    assert recovered.started_at is None
    assert recovered.completed_at is None
    assert recovered.device_id == task.device_id
    assert recovered.module_id == task.module_id
    assert recovered.action_id == task.action_id
    assert recovered.parameters == task.parameters

@pytest.mark.parametrize(
    "status",
    [
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    ],
)
def test_task_repository_recover_preserves_terminal_task_state(
    tmp_path,
    status,
):
    from app.core.task_repository import TaskRepository

    db_path = tmp_path / "tasks.db"
    repository = TaskRepository(db_path)

    task = Task(
        device_id="device:recovery-terminal-001",
        module_id="adb",
        action_id="probe",
        id=f"task:recovery-{status.value}",
    )

    if status is TaskStatus.CANCELLED:
        task.cancel()
    else:
        task.start()

        if status is TaskStatus.COMPLETED:
            task.complete(
                ActionResult(
                    success=True,
                    message="completed",
                )
            )
        else:
            task.fail(
                ActionResult(
                    success=False,
                    message="failed",
                )
            )

    repository.save(task)

    recovered = repository.recover(task.id)

    assert recovered is not None
    assert recovered.status is status
    assert recovered.attempts == task.attempts
    assert recovered.result == task.result

def test_task_repository_lists_persisted_tasks(tmp_path):
    from app.core.task_repository import TaskRepository

    db_path = tmp_path / "tasks.db"
    repository = TaskRepository(db_path)

    first = Task(
        device_id="device:list-001",
        module_id="adb",
        action_id="probe",
        id="task:list-001",
    )
    second = Task(
        device_id="device:list-002",
        module_id="fastboot",
        action_id="probe",
        id="task:list-002",
    )

    repository.save(first)
    repository.save(second)

    tasks = repository.list()

    assert {task.id for task in tasks} == {
        "task:list-001",
        "task:list-002",
    }

def test_task_repository_recovers_all_running_tasks_as_pending(tmp_path):
    from app.core.task_repository import TaskRepository

    db_path = tmp_path / "tasks.db"
    repository = TaskRepository(db_path)

    running = Task(
        device_id="device:recover-all-001",
        module_id="adb",
        action_id="probe",
        id="task:recover-all-running",
    )
    completed = Task(
        device_id="device:recover-all-002",
        module_id="adb",
        action_id="probe",
        id="task:recover-all-completed",
    )

    repository.save(running)
    repository.save(completed)

    running.start()
    repository.update(running)

    completed.start()
    completed.complete(
        ActionResult(
            success=True,
            message="completed",
        )
    )
    repository.update(completed)

    recovered = repository.recover_all()

    recovered_by_id = {task.id: task for task in recovered}

    assert recovered_by_id["task:recover-all-running"].status is TaskStatus.PENDING
    assert recovered_by_id["task:recover-all-running"].attempts == 1

    assert recovered_by_id["task:recover-all-completed"].status is TaskStatus.COMPLETED
