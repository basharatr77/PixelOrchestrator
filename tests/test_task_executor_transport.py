from app.core.module_contract import Device, DeviceState, ModuleType
from app.agents.orchestrator.task_executor import TaskExecutor
from app.core.adb_transport import ADBTransport
from app.core.fastboot_transport import FastbootTransport


class FakeTransport:
    def __init__(self, serial):
        self.serial = serial
        self.executed_commands = []

    def execute(self, command):
        self.executed_commands.append(command)

        return {
            "returncode": 0,
            "stdout": "probe-ok\n",
            "stderr": "",
        }


class FakeTransportResolver:
    transports = {}

    @staticmethod
    def resolve(device):
        transport = FakeTransport(device.serial)
        FakeTransportResolver.transports[device.serial] = transport
        return transport


def test_task_executor_execute_resolves_transport():
    executor = TaskExecutor(
        transport_resolver=FakeTransportResolver,
    )

    task = {
        "action": "safe_probe",
        "serial": "A52",
        "mode": "ADB",
    }

    result = executor.execute(task)

    transport = FakeTransportResolver.transports["A52"]

    assert transport.serial == "A52"
    assert transport.executed_commands == ["getprop ro.product.model"]
    assert result == {
        "success": True,
        "action": "safe_probe",
        "serial": "A52",
        "returncode": 0,
        "stdout": "probe-ok\n",
        "stderr": "",
    }
