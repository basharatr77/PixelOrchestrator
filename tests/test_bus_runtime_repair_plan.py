from app.core.bus_runtime import BusRuntime
from app.core.module_contract import Device, DeviceState, ModuleType


def test_bus_runtime_reconciliation_exposes_repair_plan():
    runtime = BusRuntime()

    runtime.device_registry.register(
        Device(
            device_id="device:PIXEL_PLAN_47C",
            module_type=ModuleType.ADB,
            state=DeviceState.ADB,
            serial="PIXEL_PLAN_47C",
            transport="adb",
        )
    )

    changes = runtime.reconcile_devices(
        {
            "PIXEL_PLAN_47C": "FASTBOOT",
        }
    )

    assert changes[0]["decision"] == "SAFE_TO_REPAIR"
    assert changes[0]["repair_plan"].serial == "PIXEL_PLAN_47C"
    assert changes[0]["repair_plan"].current_state is DeviceState.ADB
    assert changes[0]["repair_plan"].observed_state is DeviceState.FASTBOOT
    assert changes[0]["repair_plan"].action == "RECONCILE_STATE"
from app.core.bus_runtime import BusRuntime


def test_bus_runtime_reconciliation_does_not_plan_unknown_device():
    runtime = BusRuntime()

    changes = runtime.reconcile_devices(
        {
            "PIXEL_UNKNOWN_47C": "FASTBOOT",
        }
    )

    assert changes == [
        {
            "serial": "PIXEL_UNKNOWN_47C",
            "previous_state": None,
            "state": runtime.reconciler.MODE_TO_STATE["FASTBOOT"],
            "decision": "UNKNOWN",
        }
    ]
