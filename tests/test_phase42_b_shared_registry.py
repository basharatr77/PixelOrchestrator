from app.agents.orchestrator.task_executor import TaskExecutor
from app.core.bus_runtime import BusRuntime
from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType


def test_bus_runtime_default_task_executor_shares_device_registry():
    runtime = BusRuntime()

    assert runtime.device_registry is runtime.task_executor.device_registry

    device_a = Device(
        device_id="device:42B-A",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="42B-A",
        transport="adb",
    )
    device_b = Device(
        device_id="device:42B-B",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="42B-B",
        transport="adb",
    )

    runtime.device_registry.register(device_a)
    runtime.device_registry.register(device_b)

    assert runtime.task_executor.device_registry.get("device:42B-A") is device_a
    assert runtime.task_executor.device_registry.get("device:42B-B") is device_b


def test_bus_runtime_custom_task_executor_and_registry_are_preserved():
    custom_registry = DeviceRegistry()
    custom_executor = TaskExecutor(device_registry=custom_registry)

    runtime = BusRuntime(task_executor=custom_executor)

    assert runtime.task_executor is custom_executor
    assert runtime.task_executor.device_registry is custom_registry
    assert runtime.device_registry is not custom_registry
