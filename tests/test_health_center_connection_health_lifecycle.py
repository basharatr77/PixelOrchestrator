from app.agents.orchestrator.lifecycle_consumer import LifecycleConsumer
from app.agents.orchestrator.task_queue import TaskQueue
from app.core.device_registry import DeviceRegistry
from app.core.events import Event
from app.core.module_contract import Device, DeviceState, ModuleType


def test_disconnected_event_transitions_canonical_device_to_disconnected():
    registry = DeviceRegistry()
    queue = TaskQueue()

    device = Device(
        device_id="device:CONN_STEP21",
        module_type=ModuleType.ADB,
        state=DeviceState.ADB,
        serial="CONN_STEP21",
        transport="adb",
    )
    registry.register(device)

    consumer = LifecycleConsumer(
        task_queue=queue,
        registry_updater=lambda device, status, offset: True,
        device_registry=registry,
    )

    event = Event(
        "DEVICE_DISCONNECTED",
        {
            "serial": "CONN_STEP21",
        },
    )

    consumer.handle(event, 21, "orchestrator")

    assert registry.get("device:CONN_STEP21") is device
    assert device.state is DeviceState.DISCONNECTED
    assert device.transport == "adb"
    assert queue.tasks == []
