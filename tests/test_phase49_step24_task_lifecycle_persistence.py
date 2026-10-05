from app.core.bus_runtime import BusRuntime
from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus
from app.core.task_repository import TaskRepository


class _SuccessModule:
    id = "test-module"

    def get_actions(self):
        class _Action:
            id = "test-action"
            requires_device = False

        return [_Action()]

    def execute(self, action_id, device=None, **parameters):
        return ActionResult(
            success=True,
            message="Task completed.",
        )


class _SuccessRegistry:
    def get(self, module_id):
        if module_id == "test-module":
            return _SuccessModule()
        return None


def test_bus_runtime_persists_completed_task_after_execution(tmp_path):
    db_path = tmp_path / "tasks.db"
    repository = TaskRepository(db_path)

    task = Task(
        device_id="device-24",
        module_id="test-module",
        action_id="test-action",
    )
    repository.save(task)

    runtime = BusRuntime(task_repository=repository)
    runtime.task_executor.module_registry = _SuccessRegistry()

    result = runtime.execute_once(task)

    assert result.success is True

    persisted = repository.get(task.id)

    assert persisted is not None
    assert persisted.status is TaskStatus.COMPLETED
    assert persisted.attempts == 1
    assert persisted.result is not None
    assert persisted.result.success is True
    assert persisted.completed_at is not None
