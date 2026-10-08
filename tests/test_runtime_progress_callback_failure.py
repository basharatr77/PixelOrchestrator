from types import SimpleNamespace

from app.agents.orchestrator.task_executor import TaskExecutor
from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus


def test_progress_callback_failure_does_not_leave_successful_task_running(
    caplog,
):
    class _SuccessModule:
        def get_actions(self):
            return [SimpleNamespace(id="run", requires_device=False)]

        def execute(self, action_id, device=None, **parameters):
            return ActionResult(success=True, message="action completed")

    class _ModuleRegistry:
        def get(self, module_id):
            return _SuccessModule()

    def fail_progress_callback(_task, progress, _message):
        if progress == 100:
            raise RuntimeError("progress sink unavailable")

    task = Task(
        device_id="device:callback-failure",
        module_id="callback-failure-module",
        action_id="run",
    )
    executor = TaskExecutor(
        module_registry=_ModuleRegistry(),
        progress_callback=fail_progress_callback,
    )

    result = executor.execute(task)

    assert result.success is True
    assert task.status is TaskStatus.COMPLETED
    assert task.result is result
    assert any(
        record.message == "Task progress callback failed"
        and record.task_id == task.id
        and record.failure_type == "RuntimeError"
        for record in caplog.records
    )
