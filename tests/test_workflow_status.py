from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus
from app.core.workflow import Workflow


def make_task(action_id="probe"):
    return Task(
        device_id="device-1",
        module_id="common",
        action_id=action_id,
    )


def test_workflow_status_is_pending_when_tasks_are_pending():
    workflow = Workflow(tasks=[make_task()])
    assert workflow.status() == "pending"


def test_workflow_status_is_running_when_task_is_running():
    task = make_task()
    workflow = Workflow(tasks=[task])

    task.start()

    assert workflow.status() == "running"


def test_workflow_status_is_completed_when_all_tasks_complete():
    task = make_task()
    workflow = Workflow(tasks=[task])

    task.start()
    task.complete(ActionResult(success=True, message="done"))

    assert workflow.status() == "completed"


def test_workflow_status_is_failed_when_any_task_fails():
    task1 = make_task("probe")
    task2 = make_task("shell")
    workflow = Workflow(tasks=[task1, task2])

    task1.start()
    task1.fail(ActionResult(
        success=False,
        message="failed",
        error_code="TEST_FAILURE",
    ))

    assert workflow.status() == "failed"


def test_workflow_status_is_cancelled_when_task_is_cancelled_without_failure():
    task1 = make_task("probe")
    task2 = make_task("shell")
    workflow = Workflow(tasks=[task1, task2])

    task1.cancel()

    assert workflow.status() == "cancelled"


def test_workflow_failure_takes_precedence_over_cancellation():
    task1 = make_task("probe")
    task2 = make_task("shell")
    workflow = Workflow(tasks=[task1, task2])

    task1.start()
    task1.fail(ActionResult(
        success=False,
        message="failed",
        error_code="TEST_FAILURE",
    ))
    task2.cancel()

    assert workflow.status() == "failed"


def test_workflow_status_is_pending_when_dependency_is_blocked_but_no_task_failed():
    task1 = make_task("probe")
    task2 = make_task("shell")
    workflow = Workflow(
        tasks=[task1, task2],
        dependencies={task2.id: {task1.id}},
    )

    assert workflow.status() == "pending"
