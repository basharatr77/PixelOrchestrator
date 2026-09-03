from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus
from app.core.workflow import Workflow


def make_task(action_id):
    return Task(
        device_id="device-1",
        module_id="adb",
        action_id=action_id,
    )


def complete_task(task):
    task.start()
    task.complete(
        ActionResult(
            success=True,
            message="done",
        )
    )


def fail_task(task):
    task.start()
    task.fail(
        ActionResult(
            success=False,
            message="failed",
        )
    )


def test_workflow_progress_empty_workflow_is_zero():
    workflow = Workflow()

    assert workflow.progress() == 0


def test_workflow_progress_with_no_completed_tasks_is_zero():
    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(tasks=[task1, task2])

    assert workflow.progress() == 0


def test_workflow_progress_counts_completed_tasks():
    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(tasks=[task1, task2])

    complete_task(task1)

    assert workflow.progress() == 50


def test_workflow_progress_reaches_100_when_all_tasks_complete():
    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(tasks=[task1, task2])

    complete_task(task1)
    complete_task(task2)

    assert workflow.progress() == 100


def test_workflow_progress_does_not_count_failed_or_cancelled_tasks():
    task1 = make_task("probe")
    task2 = make_task("shell")
    task3 = make_task("reboot")
    task4 = make_task("status")

    workflow = Workflow(
        tasks=[task1, task2, task3, task4],
    )

    complete_task(task1)
    fail_task(task2)
    task3.cancel()

    assert task4.status is TaskStatus.PENDING
    assert workflow.progress() == 25
