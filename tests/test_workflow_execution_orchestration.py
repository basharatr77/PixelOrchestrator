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

