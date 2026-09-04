from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    Device,
    DeviceState,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.core.task import Task, TaskStatus
from app.core.workflow import Workflow
from app.core.bus_runtime import BusRuntime


class WorkflowTestModule(ModuleContract):
    def __init__(self):
        self.calls = []

        self.manifest = ModuleManifest(
            id="workflow-test-module",
            name="Workflow Test Module",
            version="1.0.0",
            module_type=ModuleType.COMMON,
            capabilities=(
                Capability(
                    id="workflow_test",
                    name="Workflow Test",
                ),
            ),
            actions=(
                Action(
                    id="step",
                    name="Step",
                    capability_id="workflow_test",
                ),
            ),
        )

    def execute(self, action_id, device=None, **kwargs):
        self.calls.append(kwargs.get("step"))
        return ActionResult(
            success=True,
            message="completed",
            data={"step": kwargs.get("step")},
        )


def make_runtime():
    runtime = BusRuntime()

    module = WorkflowTestModule()
    runtime.task_executor.module_registry.register(module)

    runtime.task_executor.device_registry.register(
        Device(
            device_id="workflow-device",
            module_type=ModuleType.COMMON,
            state=DeviceState.CONNECTED,
            serial="WORKFLOW",
        )
    )

    return runtime, module


def test_workflow_execution_advances_to_next_ready_task():
    runtime, module = make_runtime()

    task1 = Task(
        device_id="workflow-device",
        module_id="workflow-test-module",
        action_id="step",
        parameters={"step": "one"},
    )

    task2 = Task(
        device_id="workflow-device",
        module_id="workflow-test-module",
        action_id="step",
        parameters={"step": "two"},
    )

    workflow = Workflow(
        id="workflow-i-c",
        tasks=[task1, task2],
        dependencies={
            task2.id: {task1.id},
        },
    )

    runtime.enqueue_workflow_ready_tasks(workflow)

    assert runtime.task_queue.peek_task() is task1

    runtime.execute_once()

    assert task1.status is TaskStatus.COMPLETED

    assert runtime.task_queue.peek_task() is task2


def test_workflow_ready_task_is_not_enqueued_twice():
    runtime, module = make_runtime()

    task = Task(
        device_id="workflow-device",
        module_id="workflow-test-module",
        action_id="step",
        parameters={"step": "one"},
    )

    workflow = Workflow(
        id="workflow-i-c-duplicate",
        tasks=[task],
    )

    runtime.enqueue_workflow_ready_tasks(workflow)
    runtime.enqueue_workflow_ready_tasks(workflow)

    assert runtime.task_queue.tasks == [task]
from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    Device,
    DeviceState,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.core.task import Task
from app.core.workflow import Workflow
from app.core.bus_runtime import BusRuntime


class WorkflowIsolationModule(ModuleContract):
    def __init__(self):
        self.manifest = ModuleManifest(
            id="workflow-isolation-module",
            name="Workflow Isolation Module",
            version="1.0.0",
            module_type=ModuleType.COMMON,
            capabilities=(
                Capability(
                    id="workflow_isolation",
                    name="Workflow Isolation",
                ),
            ),
            actions=(
                Action(
                    id="step",
                    name="Step",
                    capability_id="workflow_isolation",
                ),
            ),
        )

    def execute(self, action_id, device=None, **kwargs):
        return ActionResult(
            success=True,
            message="completed",
            data={"step": kwargs.get("step")},
        )


def make_isolation_runtime():
    runtime = BusRuntime()

    runtime.task_executor.module_registry.register(
        WorkflowIsolationModule()
    )

    runtime.task_executor.device_registry.register(
        Device(
            device_id="workflow-device",
            module_type=ModuleType.COMMON,
            state=DeviceState.CONNECTED,
            serial="WORKFLOW",
        )
    )

    return runtime


def make_task(step):
    return Task(
        device_id="workflow-device",
        module_id="workflow-isolation-module",
        action_id="step",
        parameters={"step": step},
    )


def test_multiple_workflows_are_scheduled_independently():
    runtime = make_isolation_runtime()

    workflow_a_task = make_task("workflow-a")
    workflow_b_task = make_task("workflow-b")

    workflow_a = Workflow(
        id="workflow-a",
        tasks=[workflow_a_task],
    )

    workflow_b = Workflow(
        id="workflow-b",
        tasks=[workflow_b_task],
    )

    runtime.enqueue_workflow_ready_tasks(workflow_a)
    runtime.enqueue_workflow_ready_tasks(workflow_b)

    assert runtime.task_queue.tasks == [
        workflow_a_task,
        workflow_b_task,
    ]


def test_workflow_completion_automatically_publishes_terminal_outcome():
    runtime, module = make_runtime()

    task = Task(
        device_id="workflow-device",
        module_id="workflow-test-module",
        action_id="step",
        parameters={"step": "complete"},
    )

    workflow = Workflow(
        id="workflow-i-d-completed",
        tasks=[task],
    )

    events = []

    runtime.bus.subscribe(
        "test-workflow-i-d-completed",
        "WORKFLOW_COMPLETED",
        lambda event, offset, group_id: events.append(event),
    )

    runtime.enqueue_workflow_ready_tasks(workflow)
    runtime.execute_once()

    assert task.status is TaskStatus.COMPLETED
    assert workflow.status() == "completed"

    queued_events = []
    while not runtime.bus.queue.empty():
        offset, event = runtime.bus.queue.get_nowait()
        queued_events.append(event)

    assert any(event.type == "TASK_EXECUTED" for event in queued_events)
    terminal_events = [
        event for event in queued_events
        if event.type == "WORKFLOW_COMPLETED"
    ]
    assert len(terminal_events) == 1
    assert terminal_events[0].payload == {
        "workflow_id": workflow.id,
        "status": "completed",
    }
    assert event.payload == {
        "workflow_id": workflow.id,
        "status": "completed",
    }


class WorkflowFailureModule(ModuleContract):
    def __init__(self):
        self.manifest = ModuleManifest(
            id="workflow-failure-module",
            name="Workflow Failure Module",
            version="1.0.0",
            module_type=ModuleType.COMMON,
            capabilities=(
                Capability(
                    id="workflow_failure",
                    name="Workflow Failure",
                ),
            ),
            actions=(
                Action(
                    id="fail",
                    name="Fail",
                    capability_id="workflow_failure",
                    requires_device=False,
                ),
            ),
        )

    def execute(self, action_id, device=None, **kwargs):
        return ActionResult(
            success=False,
            message="workflow task failed",
            error_code="WORKFLOW_TEST_FAILURE",
        )


def test_workflow_failure_automatically_publishes_terminal_outcome():
    runtime = BusRuntime()

    runtime.task_executor.module_registry.register(
        WorkflowFailureModule()
    )

    task = Task(
        device_id="workflow-device",
        module_id="workflow-failure-module",
        action_id="fail",
    )

    workflow = Workflow(
        id="workflow-i-d-failed",
        tasks=[task],
    )

    events = []

    runtime.bus.subscribe(
        "test-workflow-i-d-failed",
        "WORKFLOW_FAILED",
        lambda event, offset, group_id: events.append(event),
    )

    runtime.enqueue_workflow_ready_tasks(workflow)
    runtime.execute_once()

    assert task.status is TaskStatus.FAILED
    assert workflow.status() == "failed"

    queued_events = []
    while not runtime.bus.queue.empty():
        offset, event = runtime.bus.queue.get_nowait()
        queued_events.append(event)

    assert any(event.type == "TASK_EXECUTED" for event in queued_events)
    terminal_events = [
        event for event in queued_events
        if event.type == "WORKFLOW_FAILED"
    ]
    assert len(terminal_events) == 1
    assert terminal_events[0].payload == {
        "workflow_id": workflow.id,
        "status": "failed",
    }
    assert event.payload == {
        "workflow_id": workflow.id,
        "status": "failed",
    }


def test_non_terminal_workflow_does_not_publish_terminal_outcome():
    runtime, module = make_runtime()

    task1 = Task(
        device_id="workflow-device",
        module_id="workflow-test-module",
        action_id="step",
        parameters={"step": "one"},
    )

    task2 = Task(
        device_id="workflow-device",
        module_id="workflow-test-module",
        action_id="step",
        parameters={"step": "two"},
    )

    workflow = Workflow(
        id="workflow-i-d-non-terminal",
        tasks=[task1, task2],
        dependencies={
            task2.id: {task1.id},
        },
    )

    runtime.enqueue_workflow_ready_tasks(workflow)
    runtime.execute_once()

    assert task1.status is TaskStatus.COMPLETED
    assert task2.status is TaskStatus.PENDING
    assert workflow.status() == "pending"

    events = []
    while not runtime.bus.queue.empty():
        offset, event = runtime.bus.queue.get_nowait()
        if event.type in {
            "WORKFLOW_COMPLETED",
            "WORKFLOW_FAILED",
            "WORKFLOW_CANCELLED",
        }:
            events.append(event)

    assert events == []
    assert runtime.task_queue.peek_task() is task2
