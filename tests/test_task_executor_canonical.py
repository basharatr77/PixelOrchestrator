import pytest

from app.core.module_contract import (
    Action,
    ActionResult,
    Device,
    DeviceState,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.core.task import Task, TaskStatus
from app.agents.orchestrator.task_executor import TaskExecutor


class FakeModule(ModuleContract):
    manifest = ModuleManifest(
        id="fake",
        name="Fake",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        actions=(
            Action(
                id="probe",
                name="Probe",
                capability_id=None,
                requires_device=True,
            ),
            Action(
                id="refresh",
                name="Refresh",
                capability_id=None,
                requires_device=False,
            ),
        ),
    )

    def detect(self):
        return []

    def execute(self, action_id, device=None, **kwargs):
        if action_id == "probe":
            assert device is not None
            assert device.device_id == "device:PIXEL_8"
            assert kwargs == {"mode": "safe"}

            return ActionResult(
                success=True,
                message="probe complete",
                data={"serial": device.serial},
            )

        if action_id == "refresh":
            assert device is None
            assert kwargs == {"scope": "all"}

            return ActionResult(
                success=True,
                message="refresh complete",
            )

        return ActionResult(
            success=False,
            message="unknown",
            error_code="UNKNOWN_ACTION",
        )


class FakeModuleRegistry:
    def __init__(self, module=None):
        self.module = module if module is not None else FakeModule()

    def get(self, module_id):
        if module_id in {"fake", self.module.manifest.id}:
            return self.module
        return None


class FakeDeviceRegistry:
    def __init__(self):
        self.device = Device(
            device_id="device:PIXEL_8",
            module_type=ModuleType.COMMON,
            state=DeviceState.CONNECTED,
            serial="PIXEL_8",
        )

    def get(self, device_id):
        if device_id == "device:PIXEL_8":
            return self.device
        return None


def make_executor():
    return TaskExecutor(
        module_registry=FakeModuleRegistry(),
        device_registry=FakeDeviceRegistry(),
    )


def test_canonical_task_executes_and_completes():
    executor = make_executor()

    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="probe",
        parameters={"mode": "safe"},
    )

    result = executor.execute(task)

    assert result is task.result
    assert result.success is True
    assert result.message == "probe complete"
    assert result.data == {"serial": "PIXEL_8"}

    assert task.status is TaskStatus.COMPLETED
    assert task.attempts == 1
    assert task.started_at is not None
    assert task.completed_at is not None


def test_canonical_task_executes_device_optional_action():
    executor = make_executor()

    task = Task(
        device_id="device:OPTIONAL",
        module_id="fake",
        action_id="refresh",
        parameters={"scope": "all"},
    )

    result = executor.execute(task)

    assert result.success is True
    assert result.message == "refresh complete"
    assert task.status is TaskStatus.COMPLETED
    assert task.attempts == 1


def test_unknown_module_returns_controlled_failure():
    executor = make_executor()

    task = Task(
        device_id="device:PIXEL_8",
        module_id="missing",
        action_id="probe",
    )

    result = executor.execute(task)

    assert result.success is False
    assert result.error_code == "MODULE_NOT_FOUND"
    assert task.status is TaskStatus.FAILED
    assert task.attempts == 1


def test_missing_required_device_returns_controlled_failure():
    executor = make_executor()

    task = Task(
        device_id="missing-device",
        module_id="fake",
        action_id="probe",
    )

    result = executor.execute(task)

    assert result.success is False
    assert result.error_code == "DEVICE_NOT_FOUND"
    assert task.status is TaskStatus.FAILED
    assert task.attempts == 1


def test_unknown_action_returns_controlled_failure():
    executor = make_executor()

    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="missing_action",
    )

    result = executor.execute(task)

    assert result.success is False
    assert result.error_code == "ACTION_NOT_FOUND"
    assert task.status is TaskStatus.FAILED
    assert task.attempts == 1


def test_module_failure_completes_as_failed_task():
    class FailingModule(FakeModule):
        def execute(self, action_id, device=None, **kwargs):
            return ActionResult(
                success=False,
                message="operation failed",
                error_code="OPERATION_FAILED",
            )

    class FailingModuleRegistry:
        def get(self, module_id):
            return FailingModule()

    executor = TaskExecutor(
        module_registry=FailingModuleRegistry(),
        device_registry=FakeDeviceRegistry(),
    )

    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="probe",
    )

    result = executor.execute(task)

    assert result.success is False
    assert result.error_code == "OPERATION_FAILED"
    assert task.status is TaskStatus.FAILED
    assert task.result is result
    assert task.attempts == 1


def test_unexpected_module_exception_becomes_failed_task():
    class ExplodingModule(FakeModule):
        def execute(self, action_id, device=None, **kwargs):
            raise RuntimeError("boom")

    class ExplodingModuleRegistry:
        def get(self, module_id):
            return ExplodingModule()

    executor = TaskExecutor(
        module_registry=ExplodingModuleRegistry(),
        device_registry=FakeDeviceRegistry(),
    )

    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="probe",
    )

    result = executor.execute(task)

    assert result.success is False
    assert result.error_code == "EXECUTION_ERROR"
    assert "boom" in result.message
    assert task.status is TaskStatus.FAILED
    assert task.attempts == 1

def test_canonical_task_retries_until_success():
    from app.core.module_contract import Action, ActionResult, ModuleManifest, ModuleType
    from app.core.retry_policy import RetryPolicy
    from app.core.task import Task, TaskStatus

    class FlakyModule:
        def __init__(self):
            self.calls = 0
            self.manifest = ModuleManifest(
                id="flaky",
                name="Flaky",
                version="1.0",
                module_type=ModuleType.COMMON,
                actions=(
                    Action(
                        id="probe",
                        name="Probe",
                        requires_device=False,
                    ),
                ),
            )

        def get_actions(self):
            return self.manifest.actions

        def execute(self, action_id, device=None, **parameters):
            self.calls += 1
            if self.calls < 3:
                return ActionResult(
                    success=False,
                    message=f"failure-{self.calls}",
                    error_code="TRANSIENT_FAILURE",
                )
            return ActionResult(
                success=True,
                message="success",
            )

    module = FlakyModule()
    executor = TaskExecutor(
        module_registry=FakeModuleRegistry(module),
        device_registry=FakeDeviceRegistry(),
    )
    task = Task(
        device_id="device:optional",
        module_id="flaky",
        action_id="probe",
    )

    executor.retry_policy = RetryPolicy(max_attempts=3)
    result = executor.execute(task)

    assert result.success is True
    assert result.message == "success"
    assert module.calls == 3
    assert task.attempts == 3
    assert task.status is TaskStatus.COMPLETED


def test_canonical_task_stops_after_max_attempts():
    from app.core.module_contract import Action, ActionResult, ModuleManifest, ModuleType
    from app.core.retry_policy import RetryPolicy
    from app.core.task import Task, TaskStatus

    class AlwaysFailModule:
        def __init__(self):
            self.calls = 0
            self.manifest = ModuleManifest(
                id="always-fail",
                name="Always Fail",
                version="1.0",
                module_type=ModuleType.COMMON,
                actions=(
                    Action(
                        id="probe",
                        name="Probe",
                        requires_device=False,
                    ),
                ),
            )

        def get_actions(self):
            return self.manifest.actions

        def execute(self, action_id, device=None, **parameters):
            self.calls += 1
            return ActionResult(
                success=False,
                message=f"failure-{self.calls}",
                error_code="TRANSIENT_FAILURE",
            )

    module = AlwaysFailModule()
    executor = TaskExecutor(
        module_registry=FakeModuleRegistry(module),
        device_registry=FakeDeviceRegistry(),
    )
    task = Task(
        device_id="device:optional",
        module_id="always-fail",
        action_id="probe",
    )

    executor.retry_policy = RetryPolicy(max_attempts=3)
    result = executor.execute(task)

    assert result.success is False
    assert result.error_code == "TRANSIENT_FAILURE"
    assert module.calls == 3
    assert task.attempts == 3
    assert task.status is TaskStatus.FAILED


def test_canonical_task_single_attempt_preserves_existing_failure_behavior():
    from app.core.module_contract import Action, ActionResult, ModuleManifest, ModuleType
    from app.core.retry_policy import RetryPolicy
    from app.core.task import Task, TaskStatus

    class FailModule:
        def __init__(self):
            self.calls = 0
            self.manifest = ModuleManifest(
                id="single-fail",
                name="Single Fail",
                version="1.0",
                module_type=ModuleType.COMMON,
                actions=(
                    Action(
                        id="probe",
                        name="Probe",
                        requires_device=False,
                    ),
                ),
            )

        def get_actions(self):
            return self.manifest.actions

        def execute(self, action_id, device=None, **parameters):
            self.calls += 1
            return ActionResult(
                success=False,
                message="failed",
                error_code="TEST_FAILURE",
            )

    module = FailModule()
    executor = TaskExecutor(
        module_registry=FakeModuleRegistry(module),
        device_registry=FakeDeviceRegistry(),
    )
    task = Task(
        device_id="device:optional",
        module_id="single-fail",
        action_id="probe",
    )

    executor.retry_policy = RetryPolicy(max_attempts=1)
    result = executor.execute(task)

    assert result.success is False
    assert module.calls == 1
    assert task.attempts == 1
    assert task.status is TaskStatus.FAILED


def test_canonical_task_retry_does_not_expose_intermediate_failure_as_terminal():
    from app.core.module_contract import Action, ActionResult, ModuleManifest, ModuleType
    from app.core.retry_policy import RetryPolicy
    from app.core.task import Task, TaskStatus

    class FlakyModule:
        def __init__(self):
            self.calls = 0
            self.manifest = ModuleManifest(
                id="intermediate",
                name="Intermediate",
                version="1.0",
                module_type=ModuleType.COMMON,
                actions=(
                    Action(
                        id="probe",
                        name="Probe",
                        requires_device=False,
                    ),
                ),
            )

        def get_actions(self):
            return self.manifest.actions

        def execute(self, action_id, device=None, **parameters):
            self.calls += 1
            if self.calls == 1:
                return ActionResult(
                    success=False,
                    message="temporary",
                    error_code="TRANSIENT_FAILURE",
                )
            return ActionResult(
                success=True,
                message="recovered",
            )

    module = FlakyModule()
    executor = TaskExecutor(
        module_registry=FakeModuleRegistry(module),
        device_registry=FakeDeviceRegistry(),
    )
    task = Task(
        device_id="device:optional",
        module_id="intermediate",
        action_id="probe",
    )

    executor.retry_policy = RetryPolicy(max_attempts=2)
    result = executor.execute(task)

    assert result.success is True
    assert result.message == "recovered"
    assert module.calls == 2
    assert task.attempts == 2
    assert task.status is TaskStatus.COMPLETED

def test_canonical_task_retries_execution_exception():
    from app.core.module_contract import Action, ActionResult, ModuleManifest, ModuleType
    from app.core.retry_policy import RetryPolicy
    from app.core.task import Task, TaskStatus

    class ExceptionThenSuccessModule:
        def __init__(self):
            self.calls = 0
            self.manifest = ModuleManifest(
                id="exception-retry",
                name="Exception Retry",
                version="1.0",
                module_type=ModuleType.COMMON,
                actions=(
                    Action(
                        id="probe",
                        name="Probe",
                        requires_device=False,
                    ),
                ),
            )

        def get_actions(self):
            return self.manifest.actions

        def execute(self, action_id, device=None, **parameters):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary execution error")

            return ActionResult(
                success=True,
                message="recovered-after-exception",
            )

    module = ExceptionThenSuccessModule()
    executor = TaskExecutor(
        module_registry=FakeModuleRegistry(module),
        device_registry=FakeDeviceRegistry(),
    )
    task = Task(
        device_id="device:optional",
        module_id="exception-retry",
        action_id="probe",
    )

    executor.retry_policy = RetryPolicy(max_attempts=2)
    result = executor.execute(task)

    assert result.success is True
    assert result.message == "recovered-after-exception"
    assert module.calls == 2
    assert task.attempts == 2
    assert task.status is TaskStatus.COMPLETED

