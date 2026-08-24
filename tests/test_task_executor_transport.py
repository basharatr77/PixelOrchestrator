from app.agents.device_agent.device_model import Device
from app.agents.orchestrator.task_executor import TaskExecutor
from app.core.adb_transport import ADBTransport
from app.core.fastboot_transport import FastbootTransport


class FakeTransportResolver:
    @staticmethod
    def resolve(device):
        if device.mode == "ADB":
            return ADBTransport(device.serial)

        if device.mode == "FASTBOOT":
            return FastbootTransport(device.serial)

        raise ValueError("unsupported mode")


def test_task_executor_resolves_transport_for_adb_device():
    executor = TaskExecutor(
        transport_resolver=FakeTransportResolver,
    )

    task = {
        "action": "safe_probe",
        "serial": "A52",
        "mode": "ADB",
    }

    result = executor.resolve_transport(task)

    assert isinstance(result, ADBTransport)
    assert result.serial == "A52"


def test_task_executor_resolves_transport_for_fastboot_device():
    executor = TaskExecutor(
        transport_resolver=FakeTransportResolver,
    )

    task = {
        "action": "diagnostic_scan",
        "serial": "RF8T206R8EP",
        "mode": "FASTBOOT",
    }

    result = executor.resolve_transport(task)

    assert isinstance(result, FastbootTransport)
    assert result.serial == "RF8T206R8EP"
