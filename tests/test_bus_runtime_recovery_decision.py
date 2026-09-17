from app.core.bus_runtime import BusRuntime
from app.core.module_contract import Device, DeviceState, ModuleType


def test_bus_runtime_reconciliation_exposes_recovery_decision():
    runtime = BusRuntime()

    runtime.device_registry.register(
        Device(
            device_id="device:PIXEL_RECOVERY_47B",
            module_type=ModuleType.ADB,
            state=DeviceState.ADB,
            serial="PIXEL_RECOVERY_47B",
            transport="adb",
        )
    )

    changes = runtime.reconcile_devices(
        {
            "PIXEL_RECOVERY_47B": "FASTBOOT",
        }
    )

    assert changes[0]["decision"] == "SAFE_TO_REPAIR"
