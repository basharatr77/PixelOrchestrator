from app.core.bus_runtime import BusRuntime
from app.core.module_contract import Action, ActionResult
from app.core.task import Task, TaskStatus
from app.core.task_repository import TaskRepository


class _DangerousModule:
    id = "dangerous_persistence_test"

    def __init__(self):
        self.execute_calls = 0
        self._actions = [
            Action(
                id="protected",
                name="Protected action",
                requires_device=False,
                dangerous=True,
            )
        ]

    def get_actions(self):
        return self._actions

    def execute(self, action_id, device=None, **parameters):
        self.execute_calls += 1
        return ActionResult(
            success=True,
            message="Unexpected execution.",
        )


class _ModuleRegistry:
    def __init__(self, module):
        self.module = module

    def get(self, module_id):
        if module_id == self.module.id:
            return self.module
        return None


def test_runtime_persists_dangerous_action_rejection(tmp_path):
    repository = TaskRepository(tmp_path / "dangerous_tasks.db")
    module = _DangerousModule()

    runtime = BusRuntime(task_repository=repository)
    runtime.task_executor.module_registry = _ModuleRegistry(module)

    task = Task(
        device_id="device-dangerous-test",
        module_id=module.id,
        action_id="protected",
    )

    result = runtime.execute_once(task)

    assert result is not None
    assert result.success is False
    assert result.error_code == "DANGEROUS_ACTION_REQUIRES_APPROVAL"
    assert module.execute_calls == 0

    persisted = repository.get(task.id)

    assert persisted is not None
    assert persisted.status is TaskStatus.FAILED
    assert persisted.attempts == 1
    assert persisted.result is not None
    assert persisted.result.success is False
    assert (
        persisted.result.error_code
        == "DANGEROUS_ACTION_REQUIRES_APPROVAL"
    )
    assert persisted.completed_at is not None
