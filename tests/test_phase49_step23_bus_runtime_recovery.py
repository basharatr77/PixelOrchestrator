from app.core.bus_runtime import BusRuntime
from app.core.task import Task, TaskStatus
from app.core.task_repository import TaskRepository


def test_bus_runtime_rehydrates_persisted_tasks_after_restart(tmp_path):
    db_path = tmp_path / "tasks.db"

    repository = TaskRepository(db_path)
    task = Task(
        device_id="device-1",
        module_id="module-1",
        action_id="action-1",
        parameters={"mode": "safe"},
    )
    repository.save(task)

    runtime = BusRuntime(task_repository=repository)

    assert any(
        queued_task.id == task.id
        for queued_task in runtime.task_queue.tasks
    )
def test_bus_runtime_recovers_running_task_as_pending(tmp_path):
    db_path = tmp_path / "tasks.db"

    repository = TaskRepository(db_path)
    task = Task(
        device_id="device-2",
        module_id="module-2",
        action_id="action-2",
        parameters={"mode": "safe"},
    )
    repository.save(task)
    task.start()
    repository.update(task)

    runtime = BusRuntime(task_repository=repository)

    recovered = next(
        queued_task
        for queued_task in runtime.task_queue.tasks
        if queued_task.id == task.id
    )

    assert recovered.status is TaskStatus.PENDING
    assert recovered.id == task.id
    assert recovered.attempts == 1
    assert recovered.started_at is None
    assert recovered.completed_at is None
    assert recovered.result is None
