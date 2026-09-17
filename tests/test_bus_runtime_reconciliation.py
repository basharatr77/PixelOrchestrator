
from app.core.bus_runtime import BusRuntime
from app.core.module_contract import Device, DeviceState, ModuleType


def test_bus_runtime_reconciliation_uses_canonical_device_registry():
    runtime = BusRuntime()

    runtime.device_registry.register(
        Device(
            device_id="device:PIXEL_RECON_8",
            module_type=ModuleType.ADB,
            state=DeviceState.ADB,
            serial="PIXEL_RECON_8",
            transport="adb",
        )
    )

    changes = runtime.reconcile_devices(
        {
            "PIXEL_RECON_8": "FASTBOOT",
        }
    )

    assert changes == [
        {
            "serial": "PIXEL_RECON_8",
            "previous_state": DeviceState.ADB,
            "state": DeviceState.FASTBOOT,
        }
    ]

    assert runtime.device_registry.get("device:PIXEL_RECON_8").state == DeviceState.FASTBOOT
