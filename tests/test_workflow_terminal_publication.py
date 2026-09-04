from app.core.module_contract import ActionResult
from app.core.bus_runtime import BusRuntime
from app.core.task import Task
from app.core.workflow import Workflow
import asyncio


def make_task(task_id):
    return Task(
        id=task_id,
        device_id="device-1",
        module_id="module-1",
        action_id="action-1",
    )


def make_completed_workflow():
    task = make_task("task-a")
    task.start()
    task.complete(ActionResult(success=True, message="completed"))

    return Workflow(
        id="workflow-completed-event",
        tasks=[task],
    )


def make_failed_workflow():
    task = make_task("task-a")
    task.start()
    task.fail(ActionResult(
        success=False,
        message="failed",
        error_code="TEST_FAILURE",
    ))

    return Workflow(
        id="workflow-failed-event",
        tasks=[task],
    )


def make_cancelled_workflow():
    task = make_task("task-a")
    task.cancel()

    return Workflow(
        id="workflow-cancelled-event",
        tasks=[task],
    )


def dispatch_published_event(runtime):
    offset, event = runtime.bus.queue.get_nowait()
    asyncio.run(runtime.bus.dispatch(offset, event))


def test_completed_workflow_publishes_terminal_outcome():
    runtime = BusRuntime()
    events = []

    runtime.bus.subscribe(
        "test-workflow-completed",
        "WORKFLOW_COMPLETED",
        lambda event, offset, group_id: events.append(event),
    )

    workflow = make_completed_workflow()

    runtime.publish_workflow_terminal_outcome(workflow)
    dispatch_published_event(runtime)

    assert len(events) == 1
    assert events[0].type == "WORKFLOW_COMPLETED"
    assert events[0].payload == {
        "workflow_id": workflow.id,
        "status": "completed",
    }


def test_failed_workflow_publishes_terminal_outcome():
    runtime = BusRuntime()
    events = []

    runtime.bus.subscribe(
        "test-workflow-failed",
        "WORKFLOW_FAILED",
        lambda event, offset, group_id: events.append(event),
    )

    workflow = make_failed_workflow()

    runtime.publish_workflow_terminal_outcome(workflow)
    dispatch_published_event(runtime)

    assert len(events) == 1
    assert events[0].type == "WORKFLOW_FAILED"
    assert events[0].payload == {
        "workflow_id": workflow.id,
        "status": "failed",
    }


def test_cancelled_workflow_publishes_terminal_outcome():
    runtime = BusRuntime()
    events = []

    runtime.bus.subscribe(
        "test-workflow-cancelled",
        "WORKFLOW_CANCELLED",
        lambda event, offset, group_id: events.append(event),
    )

    workflow = make_cancelled_workflow()

    runtime.publish_workflow_terminal_outcome(workflow)
    dispatch_published_event(runtime)

    assert len(events) == 1
    assert events[0].type == "WORKFLOW_CANCELLED"
    assert events[0].payload == {
        "workflow_id": workflow.id,
        "status": "cancelled",
    }


def test_non_terminal_workflow_does_not_publish_terminal_outcome():
    runtime = BusRuntime()
    events = []

    for event_type in (
        "WORKFLOW_COMPLETED",
        "WORKFLOW_FAILED",
        "WORKFLOW_CANCELLED",
    ):
        runtime.bus.subscribe(
            "test-workflow-pending",
            event_type,
            lambda event, offset, group_id: events.append(event),
        )

    workflow = Workflow(
        id="workflow-pending-event",
        tasks=[make_task("task-a")],
    )

    runtime.publish_workflow_terminal_outcome(workflow)

    assert runtime.bus.queue.empty()
    assert events == []
