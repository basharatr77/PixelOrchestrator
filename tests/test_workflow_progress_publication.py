from app.core.bus_runtime import BusRuntime
from app.core.module_contract import ActionResult
from app.core.task import Task
from app.core.workflow import Workflow


def make_task(action_id):
    return Task(
        device_id="device-1",
        module_id="adb",
        action_id=action_id,
    )


def complete_task(task):
    from app.core.module_contract import ActionResult

    task.start()
    task.complete(
        ActionResult(
            success=True,
            message="done",
        )
    )


def test_g_d_workflow_progress_publication_uses_workflow_identity():
    runtime = BusRuntime()

    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(
        tasks=[task1, task2],
    )

    complete_task(task1)

    published = []
    original_publish_now = runtime.bus.publish_now

    def capture(event):
        published.append(event)
        return original_publish_now(event)

    runtime.bus.publish_now = capture

    runtime.publish_workflow_progress(workflow)

    workflow_events = [
        event
        for event in published
        if event.type == "WORKFLOW_PROGRESS"
    ]

    assert len(workflow_events) == 1

    event = workflow_events[0]

    assert event.payload["workflow_id"] == workflow.id
    assert event.payload["progress"] == 50


def test_g_d_workflow_progress_publication_does_not_replace_task_progress():
    runtime = BusRuntime()

    task = make_task("probe")
    workflow = Workflow(tasks=[task])

    runtime.publish_workflow_progress(workflow)

    event = runtime.bus.queue.get_nowait()[1]

    assert event.type == "WORKFLOW_PROGRESS"
    assert event.payload["workflow_id"] == workflow.id
    assert event.payload["progress"] == 0


def test_g_d_workflow_progress_reaches_100_when_workflow_is_complete():
    runtime = BusRuntime()

    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(
        tasks=[task1, task2],
    )

    complete_task(task1)
    complete_task(task2)

    runtime.publish_workflow_progress(workflow)

    event = runtime.bus.queue.get_nowait()[1]

    assert event.type == "WORKFLOW_PROGRESS"
    assert event.payload["workflow_id"] == workflow.id
    assert event.payload["progress"] == 100
