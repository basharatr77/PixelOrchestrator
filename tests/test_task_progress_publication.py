from app.core.bus_runtime import BusRuntime
from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.core.retry_policy import RetryPolicy
from app.core.task import Task


class ProgressModule(ModuleContract):
    def __init__(self, results=None):
        self.results = list(results or [
            ActionResult(
                success=True,
                message="completed",
            )
        ])

        self.manifest = ModuleManifest(
            id="progress-test-module",
            name="Progress Test Module",
            version="1.0",
            module_type=ModuleType.COMMON,
            capabilities=(
                Capability(
                    id="progress",
                    name="Progress",
                ),
            ),
            actions=(
                Action(
                    id="run",
                    name="Run",
                    capability_id="progress",
                    requires_device=False,
                ),
            ),
        )

    def validate_manifest(self):
        return True

    def detect(self):
        return []

    def get_capabilities(self):
        return self.manifest.capabilities

    def get_actions(self):
        return self.manifest.actions

    def execute(self, action_id, device=None, **parameters):
        return self.results.pop(0)


def _capture_events(runtime):
    published = []
    original_publish_now = runtime.bus.publish_now

    def capture(event):
        published.append(event)
        return original_publish_now(event)

    runtime.bus.publish_now = capture
    return published


def test_g_b_successful_task_publishes_progress_and_execution_events():
    runtime = BusRuntime()

    runtime.task_executor.module_registry.register(
        ProgressModule()
    )

    task = Task(
        device_id="test-device",
        module_id="progress-test-module",
        action_id="run",
    )

    published = _capture_events(runtime)

    result = runtime.execute_once(task)

    assert result.success is True

    progress_events = [
        event
        for event in published
        if event.type == "TASK_PROGRESS"
    ]

    assert [event.payload["progress"] for event in progress_events] == [
        0,
        100,
    ]

    assert all(
        event.payload["task_id"] == task.id
        for event in progress_events
    )

    assert any(
        event.type == "TASK_EXECUTED"
        for event in published
    )


def test_g_b_progress_is_per_execution_attempt():
    runtime = BusRuntime()

    progress_callback = runtime.task_executor.progress_callback

    runtime.task_executor = runtime.task_executor.__class__(
        module_registry=runtime.task_executor.module_registry,
        device_registry=runtime.device_registry,
        retry_policy=RetryPolicy(max_attempts=2),
        progress_callback=progress_callback,
    )

    runtime.execution_worker.executor = runtime.task_executor

    runtime.task_executor.module_registry.register(
        ProgressModule(
            results=[
                ActionResult(
                    success=False,
                    message="retry me",
                    error_code="TEMPORARY",
                ),
                ActionResult(
                    success=True,
                    message="completed",
                ),
            ]
        )
    )

    task = Task(
        device_id="test-device",
        module_id="progress-test-module",
        action_id="run",
    )

    published = _capture_events(runtime)

    result = runtime.execute_once(task)

    assert result.success is True

    progress_events = [
        event
        for event in published
        if event.type == "TASK_PROGRESS"
    ]

    assert [event.payload["progress"] for event in progress_events] == [
        0,
        100,
        0,
        100,
    ]

    assert all(
        event.payload["task_id"] == task.id
        for event in progress_events
    )

    assert any(
        event.type == "TASK_EXECUTED"
        for event in published
    )
