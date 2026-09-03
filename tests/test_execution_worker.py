from app.agents.orchestrator.task_executor import TaskExecutor
from app.agents.orchestrator.task_queue import TaskQueue
from app.agents.orchestrator.execution_worker import ExecutionWorker


class FakeTransport:
    def execute(self, command):
        return {
            "returncode": 0,
            "stdout": "probe-ok\n",
            "stderr": "",
        }


class FakeTransportResolver:
    @staticmethod
    def resolve(device):
        return FakeTransport()


def test_execution_worker_executes_queued_task():
    queue = TaskQueue()
    executor = TaskExecutor(
        transport_resolver=FakeTransportResolver,
    )

    queue.add_task({
        "action": "safe_probe",
        "serial": "PIXEL_8",
        "mode": "ADB",
    })

    worker = ExecutionWorker(
        task_queue=queue,
        executor=executor,
    )

    result = worker.run_once()

    assert result == {
        "success": True,
        "action": "safe_probe",
        "serial": "PIXEL_8",
        "returncode": 0,
        "stdout": "probe-ok\n",
        "stderr": "",
    }

    assert queue.tasks == []


def test_execution_worker_executes_diagnostic_task():
    queue = TaskQueue()
    executor = TaskExecutor()

    queue.add_task({
        "action": "diagnostic_scan",
        "serial": "PIXEL_8",
    })

    worker = ExecutionWorker(
        task_queue=queue,
        executor=executor,
    )

    result = worker.run_once()

    assert result == {
        "success": True,
        "action": "diagnostic_scan",
        "serial": "PIXEL_8",
    }

    assert queue.tasks == []


def test_execution_worker_returns_none_when_queue_is_empty():
    queue = TaskQueue()
    executor = TaskExecutor()

    worker = ExecutionWorker(
        task_queue=queue,
        executor=executor,
    )

    assert worker.run_once() is None
from app.agents.orchestrator.execution_worker import ExecutionWorker
from app.agents.orchestrator.task_queue import TaskQueue
from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus


class RecordingExecutor:
    def __init__(self):
        self.received = []

    def execute(self, task):
        self.received.append(task)
        task.start()
        result = ActionResult(success=True, message="worker-ok")
        task.complete(result)
        return result


def test_execution_worker_forwards_canonical_task():
    queue = TaskQueue()
    executor = RecordingExecutor()

    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="probe",
    )

    queue.add_task(task)

    worker = ExecutionWorker(
        task_queue=queue,
        executor=executor,
    )

    result = worker.run_once()

    assert executor.received == [task]
    assert result.success is True
    assert result.message == "worker-ok"
    assert task.status is TaskStatus.COMPLETED
    assert task.attempts == 1
    assert queue.tasks == []

def test_execution_worker_skips_cancelled_canonical_task():
    from app.core.task import Task, TaskStatus

    queue = TaskQueue()
    executor = RecordingExecutor()

    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="probe",
    )
    task.cancel()

    queue.add_task(task)

    worker = ExecutionWorker(
        task_queue=queue,
        executor=executor,
    )

    result = worker.run_once()

    assert result is None
    assert executor.received == []
    assert task.status is TaskStatus.CANCELLED
    assert queue.tasks == []


def test_execution_worker_does_not_execute_cancelled_task():
    from app.core.task import Task, TaskStatus

    class FailingExecutor:
        def execute(self, task):
            raise AssertionError("Cancelled task must not reach executor.")

    queue = TaskQueue()
    task = Task(
        device_id="device:PIXEL_8",
        module_id="fake",
        action_id="probe",
    )
    task.cancel()

    queue.add_task(task)

    worker = ExecutionWorker(
        task_queue=queue,
        executor=FailingExecutor(),
    )

    result = worker.run_once()

    assert result is None
    assert task.status is TaskStatus.CANCELLED
    assert task.attempts == 0
    assert queue.tasks == []
