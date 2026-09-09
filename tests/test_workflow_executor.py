from app.agents.orchestrator.task_queue import TaskQueue
from app.agents.orchestrator.workflow_executor import WorkflowExecutor
from app.core.task import Task
from app.core.workflow import Workflow


def _task(task_id):
    return Task(
        id=task_id,
        device_id="device-1",
        module_id="module-1",
        action_id="action-1",
    )


def _workflow(workflow_id, task):
    return Workflow(
        id=workflow_id,
        tasks=[task],
        dependencies={},
    )


def test_workflow_executor_enqueues_ready_tasks():
    queue = TaskQueue()
    executor = WorkflowExecutor(queue)

    task = _task("task-1")
    workflow = _workflow("workflow-1", task)

    enqueued = executor.enqueue_ready_tasks(workflow)

    assert enqueued == [task]
    assert queue.tasks == [task]


def test_workflow_executor_does_not_enqueue_blocked_tasks():
    queue = TaskQueue()
    executor = WorkflowExecutor(queue)

    dependency = _task("dependency")
    blocked = _task("blocked")

    workflow = Workflow(
        id="workflow-1",
        tasks=[dependency, blocked],
        dependencies={"blocked": ["dependency"]},
    )

    enqueued = executor.enqueue_ready_tasks(workflow)

    assert enqueued == [dependency]
    assert queue.tasks == [dependency]


def test_workflow_executor_same_id_different_workflow_does_not_duplicate_ready_task():
    queue = TaskQueue()
    executor = WorkflowExecutor(queue)

    first_task = _task("task-1")
    first_workflow = _workflow("workflow-1", first_task)

    first_enqueued = executor.enqueue_ready_tasks(first_workflow)

    replacement_task = _task("task-1")
    replacement_workflow = _workflow("workflow-1", replacement_task)

    second_enqueued = executor.enqueue_ready_tasks(replacement_workflow)

    assert first_enqueued == [first_task]
    assert second_enqueued == []
    assert queue.tasks == [first_task]
    assert executor._workflows["workflow-1"] is replacement_workflow


def test_workflow_executor_repeated_advance_does_not_duplicate_ready_task():
    queue = TaskQueue()
    executor = WorkflowExecutor(queue)

    task = _task("task-1")
    workflow = _workflow("workflow-1", task)

    first_enqueued = executor.enqueue_ready_tasks(workflow)
    second_enqueued = executor.advance()
    third_enqueued = executor.advance()

    assert first_enqueued == [task]
    assert second_enqueued == []
    assert third_enqueued == []
    assert queue.tasks == [task]

def test_workflow_executor_different_workflows_same_task_id_does_not_duplicate_ready_task():
    queue = TaskQueue()
    executor = WorkflowExecutor(queue)

    first_task = _task("shared-task")
    first_workflow = _workflow("workflow-1", first_task)

    second_task = _task("shared-task")
    second_workflow = _workflow("workflow-2", second_task)

    first_enqueued = executor.enqueue_ready_tasks(first_workflow)
    second_enqueued = executor.enqueue_ready_tasks(second_workflow)

    assert first_enqueued == [first_task]
    assert second_enqueued == []
    assert queue.tasks == [first_task]
    assert executor._workflows["workflow-1"] is first_workflow
    assert executor._workflows["workflow-2"] is second_workflow
