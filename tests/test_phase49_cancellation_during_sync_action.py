from copy import deepcopy
from types import SimpleNamespace

from app.agents.orchestrator.execution_worker import ExecutionWorker
from app.agents.orchestrator.task_executor import TaskExecutor
from app.agents.orchestrator.task_queue import TaskQueue
from app.core.bus_runtime import BusRuntime
from app.core.device_registry import DeviceRegistry
from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus


class _MemoryTaskRepository:
    def __init__(self):
        self.tasks = {}

    def get(self, task_id):
        task = self.tasks.get(task_id)
        return deepcopy(task) if task is not None else None

    def save(self, task):
        self.tasks[task.id] = deepcopy(task)

    def update(self, task):
        self.tasks[task.id] = deepcopy(task)


class _WorkflowExecutor:
    def on_task_executed(self, task):
        return []

    def terminal_workflows(self):
        return []


def test_cancellation_during_sync_action_is_persisted_as_terminal():
    task = Task(
        device_id="device:cancellation",
        module_id="cancel-module",
        action_id="sync-action",
    )

    class _CancelDuringExecutionModule:
        def get_actions(self):
            return [SimpleNamespace(id="sync-action", requires_device=False)]

        def execute(self, action_id, device=None, **parameters):
            task.cancel()
            return ActionResult(success=True, message="action returned")

    class _ModuleRegistry:
        def get(self, module_id):
            if module_id == "cancel-module":
                return _CancelDuringExecutionModule()
            return None

    repository = _MemoryTaskRepository()
    runtime = object.__new__(BusRuntime)
    runtime.task_repository = repository
    runtime.task_queue = TaskQueue()
    runtime.task_executor = TaskExecutor(
        module_registry=_ModuleRegistry(),
        device_registry=DeviceRegistry(),
    )
    runtime.execution_worker = ExecutionWorker(
        task_queue=runtime.task_queue,
        executor=runtime.task_executor,
    )
    runtime.bus = SimpleNamespace(publish_now=lambda event: None)
    runtime.workflow_executor = _WorkflowExecutor()

    result = runtime.execute_once(task)

    assert result.success is False
    assert result.error_code == "TASK_CANCELLED"
    assert task.status is TaskStatus.CANCELLED
    assert task.attempts == 1
    assert task.completed_at is not None

    persisted = repository.get(task.id)
    assert persisted.status is TaskStatus.CANCELLED
    assert persisted.result is not None
    assert persisted.result.error_code == "TASK_CANCELLED"
    assert persisted.completed_at == task.completed_at
