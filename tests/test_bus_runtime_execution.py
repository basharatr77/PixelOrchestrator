from app.agents.orchestrator.task_executor import TaskExecutor
from app.agents.orchestrator.execution_worker import ExecutionWorker
from app.core.bus_runtime import BusRuntime


def test_bus_runtime_executes_lifecycle_task():
    runtime = BusRuntime()

    runtime.setup()

    result = runtime.execute_once({
        "action": "safe_probe",
        "serial": "PIXEL_8",
    })

    assert result == {
        "success": True,
        "action": "safe_probe",
        "serial": "PIXEL_8",
    }

    assert runtime.task_queue.tasks == []
