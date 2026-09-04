from app.core.bus_runtime import BusRuntime
from app.core.module_contract import ActionResult
from app.core.task import Task
from app.core.workflow import Workflow


def make_task(task_id):
    return Task(
        id=task_id,
        device_id="device:PIXEL_8",
        module_id="test-module",
        action_id="test-action",
    )


def test_bus_runtime_exposes_workflow_executor():
    runtime = BusRuntime()

    assert runtime.workflow_executor is not None


def test_bus_runtime_enqueues_ready_workflow_tasks():
    runtime = BusRuntime()

    task = make_task("task-1")
    workflow = Workflow(tasks=[task])

    result = runtime.enqueue_workflow_ready_tasks(workflow)

    assert result == [task]
    assert runtime.task_queue.tasks == [task]


def test_bus_runtime_does_not_enqueue_blocked_workflow_tasks():
    runtime = BusRuntime()

    task1 = make_task("task-1")
    task2 = make_task("task-2")

    task1.start()
    task1.complete(ActionResult(success=True, message="done"))

    workflow = Workflow(
        tasks=[task1, task2],
        dependencies={"task-2": {"task-1"}},
    )

    result = runtime.enqueue_workflow_ready_tasks(workflow)

    assert result == [task2]
    assert runtime.task_queue.tasks == [task2]
