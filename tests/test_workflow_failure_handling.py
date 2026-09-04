from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus
from app.core.workflow import Workflow


def make_task(task_id):
    return Task(
        id=task_id,
        device_id="device-1",
        module_id="module-1",
        action_id="action-1",
    )


def test_workflow_failed_task_blocks_success_outcome():
    task_a = make_task("task-a")
    task_b = make_task("task-b")

    task_a.start()
    task_a.fail(ActionResult(success=False, message="execution failed"))

    task_b.start()
    task_b.complete(ActionResult(success=True, message="execution completed"))

    workflow = Workflow(
        id="workflow-failure-1",
        tasks=[task_a, task_b],
    )

    assert workflow.status() == "failed"


def test_workflow_cancelled_task_is_not_treated_as_failure():
    task_a = make_task("task-a")
    task_a.cancel()

    workflow = Workflow(
        id="workflow-cancel-1",
        tasks=[task_a],
    )

    assert workflow.status() == "cancelled"


def test_workflow_failed_dependency_does_not_make_dependent_task_ready():
    task_a = make_task("task-a")
    task_b = make_task("task-b")

    task_a.start()
    task_a.fail(ActionResult(success=False, message="dependency failed"))

    workflow = Workflow(
        id="workflow-dependent-failure-1",
        tasks=[task_a, task_b],
        dependencies={
            "task-b": {"task-a"},
        },
    )

    assert workflow.ready_tasks() == []


def test_workflow_failed_task_does_not_change_other_task_state():
    task_a = make_task("task-a")
    task_b = make_task("task-b")

    task_a.start()
    task_a.fail(ActionResult(success=False, message="execution failed"))

    workflow = Workflow(
        id="workflow-isolation-1",
        tasks=[task_a, task_b],
    )

    assert task_a.status is TaskStatus.FAILED
    assert task_b.status is TaskStatus.PENDING
    assert workflow.status() == "failed"
