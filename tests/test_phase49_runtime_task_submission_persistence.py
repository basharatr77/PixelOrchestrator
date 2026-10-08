from pathlib import Path
from uuid import uuid4

import pytest

from app.core.bus_runtime import BusRuntime
from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus
from app.core.task_repository import TaskRepository


_VISUALIZATION_ROOT = Path(
    r"C:\Users\AndroFixX\.codex\visualizations\2026\10\07\01a11775-c335-7b92-bba7-9f8d0def2b0f"
)


@pytest.fixture
def test_root():
    path = _VISUALIZATION_ROOT / f"pixelorchestrator-task-persistence-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


@pytest.fixture(name="tmp_path")
def _event_database_isolation_path(test_root):
    return test_root


class _SuccessModule:
    id = "test-module"

    def get_actions(self):
        class _Action:
            id = "test-action"
            requires_device = False

        return [_Action()]

    def execute(self, action_id, device=None, **parameters):
        return ActionResult(success=True, message="Task completed.")


class _SuccessRegistry:
    def get(self, module_id):
        if module_id == "test-module":
            return _SuccessModule()
        return None


def test_bus_runtime_persists_new_task_before_execution(test_root):
    db_path = test_root / "runtime.db"
    repository = TaskRepository(db_path)
    runtime = BusRuntime(task_repository=repository, database=db_path)
    runtime.task_executor.module_registry = _SuccessRegistry()
    task = Task(
        device_id="device-new",
        module_id="test-module",
        action_id="test-action",
    )

    result = runtime.execute_once(task)

    assert result.success is True
    persisted = repository.get(task.id)
    assert persisted is not None
    assert persisted.status is TaskStatus.COMPLETED
