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
