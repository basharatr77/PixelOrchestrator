from app.agents.orchestrator.task_queue import TaskQueue
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


def test_workflow_executor_enqueues_ready_tasks():
    from app.agents.orchestrator.workflow_executor import WorkflowExecutor

    task = make_task("task-1")
    workflow = Workflow(tasks=[task])
    queue = TaskQueue()

    executor = WorkflowExecutor(task_queue=queue)

    result = executor.enqueue_ready_tasks(workflow)

    assert result == [task]
    assert queue.tasks == [task]


def test_workflow_executor_does_not_enqueue_blocked_tasks():
    from app.agents.orchestrator.workflow_executor import WorkflowExecutor

    task1 = make_task("task-1")
    task2 = make_task("task-2")

    task1.start()
    task1.complete(ActionResult(success=True, message="done"))

    workflow = Workflow(
        tasks=[task1, task2],
        dependencies={
            "task-2": {"task-1"},
        },
    )

    queue = TaskQueue()
    executor = WorkflowExecutor(task_queue=queue)

    result = executor.enqueue_ready_tasks(workflow)

    assert result == [task2]
    assert queue.tasks == [task2]
