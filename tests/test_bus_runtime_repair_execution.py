from app.agents.orchestrator.task_executor import TaskExecutor
from app.core.bus_runtime import BusRuntime
from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.repair_plan import RepairPlan
from app.core.task import Task


def test_repair_plan_executes_through_canonical_runtime():
    device_registry = DeviceRegistry()
    device_registry.register(
        Device(
            device_id="device:PIXEL_8",
            module_type=ModuleType.COMMON,
            state=DeviceState.ADB,
            serial="PIXEL_8",
        )
    )

    runtime = BusRuntime(
        task_executor=TaskExecutor(
            device_registry=device_registry,
        )
    )
    runtime.task_executor.module_registry.register(
        __import__(
            "app.modules.common.module",
            fromlist=["CommonModule"],
        ).CommonModule()
    )

    plan = RepairPlan.create(
        serial="PIXEL_8",
        current_state=DeviceState.ADB,
        observed_state=DeviceState.FASTBOOT,
        decision="SAFE_TO_REPAIR",
    )

    task = Task(
        device_id="device:PIXEL_8",
        module_id="common",
        action_id="reconcile_state",
        parameters={"target_state": plan.observed_state},
    )

    result = runtime.execute_once(task)

    assert result.success is True
    assert task.status.value == "completed"
    assert device_registry.get("device:PIXEL_8").state is DeviceState.FASTBOOT

def test_bus_runtime_executes_generated_repair_plan():
    from app.modules.common.module import CommonModule

    runtime = BusRuntime()
    runtime.task_executor.module_registry.register(CommonModule())

    runtime.device_registry.register(
        Device(
            device_id="device:PIXEL_REPAIR_8",
            module_type=ModuleType.COMMON,
            state=DeviceState.ADB,
            serial="PIXEL_REPAIR_8",
        )
    )

    changes = runtime.reconcile_devices(
        {
            "PIXEL_REPAIR_8": "FASTBOOT",
        }
    )

    plan = changes[0]["repair_plan"]

    task = Task(
        device_id="device:PIXEL_REPAIR_8",
        module_id="common",
        action_id="reconcile_state",
        parameters={"target_state": plan.observed_state},
    )

    result = runtime.execute_once(task)

    assert result.success is True
    assert task.status.value == "completed"
    assert runtime.device_registry.get("device:PIXEL_REPAIR_8").state is DeviceState.FASTBOOT
