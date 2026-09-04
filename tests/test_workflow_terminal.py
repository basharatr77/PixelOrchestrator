from app.core.module_contract import ActionResult
from app.core.task import Task
from app.core.workflow import Workflow


def make_task(task_id):
    return Task(
        id=task_id,
        device_id="device-1",
        module_id="module-1",
        action_id="action-1",
    )


def test_workflow_is_not_terminal_while_pending():
    workflow = Workflow(
        id="workflow-terminal-pending",
        tasks=[make_task("task-a")],
    )

    assert workflow.status() == "pending"
    assert workflow.is_terminal() is False


def test_workflow_is_not_terminal_while_running():
    task = make_task("task-a")
    task.start()

    workflow = Workflow(
        id="workflow-terminal-running",
        tasks=[task],
    )

    assert workflow.status() == "running"
    assert workflow.is_terminal() is False


def test_workflow_is_terminal_when_completed():
    task = make_task("task-a")
    task.start()
    task.complete(ActionResult(success=True, message="completed"))

    workflow = Workflow(
        id="workflow-terminal-completed",
        tasks=[task],
    )

    assert workflow.status() == "completed"
    assert workflow.is_terminal() is True


def test_workflow_is_terminal_when_failed():
    task = make_task("task-a")
    task.start()
    task.fail(ActionResult(
        success=False,
        message="failed",
        error_code="TEST_FAILURE",
    ))

    workflow = Workflow(
        id="workflow-terminal-failed",
        tasks=[task],
    )

    assert workflow.status() == "failed"
    assert workflow.is_terminal() is True


def test_workflow_is_terminal_when_cancelled():
    task = make_task("task-a")
    task.cancel()

    workflow = Workflow(
        id="workflow-terminal-cancelled",
        tasks=[task],
    )

    assert workflow.status() == "cancelled"
    assert workflow.is_terminal() is True


def test_workflow_terminal_query_does_not_mutate_tasks():
    task_a = make_task("task-a")
    task_b = make_task("task-b")

    task_a.start()
    task_a.fail(ActionResult(
        success=False,
        message="dependency failed",
        error_code="DEPENDENCY_FAILURE",
    ))

    workflow = Workflow(
        id="workflow-terminal-isolation",
        tasks=[task_a, task_b],
        dependencies={
            "task-b": {"task-a"},
        },
    )

    before = (task_a.status, task_b.status, task_a.result)

    assert workflow.is_terminal() is True

    after = (task_a.status, task_b.status, task_a.result)
    assert after == before
