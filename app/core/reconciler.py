from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState


class Reconciler:
    """Compare observed hardware state with canonical registry state."""

    MODE_TO_STATE = {
        "ADB": DeviceState.ADB,
        "FASTBOOT": DeviceState.FASTBOOT,
        "FASTBOOTD": DeviceState.FASTBOOTD,
        "RECOVERY": DeviceState.RECOVERY,
        "SIDELOAD": DeviceState.SIDELOAD,
        "EDL": DeviceState.EDL,
        "BROM": DeviceState.BROM,
        "PRELOADER": DeviceState.PRELOADER,
        "DOWNLOAD": DeviceState.DOWNLOAD,
    }

    def __init__(self, registry: DeviceRegistry) -> None:
        if not isinstance(registry, DeviceRegistry):
            raise TypeError("registry must be a DeviceRegistry")

        self.registry = registry

    def reconcile(self, observed: dict[str, str], apply: bool = True) -> list[dict]:
        if not isinstance(observed, dict):
            raise TypeError("observed must be a dict")

        changes = []

        for serial, mode in observed.items():
            target = self.MODE_TO_STATE.get(str(mode).upper())

            if target is None:
                continue

            device = self.registry.get(f"device:{serial}")

            if device is None:
                changes.append(
                    {
                        "serial": serial,
                        "previous_state": None,
                        "state": target,
                    }
                )
                continue

            if device.state == target:
                continue

            changes.append(
                {
                    "serial": serial,
                    "previous_state": device.state,
                    "state": target,
                }
            )


            if apply:
                self.registry.update(Device(
                    device_id=device.device_id,
                    module_type=device.module_type,
                    state=target,
                    model=device.model,
                    serial=device.serial,
                    transport=device.transport,
                    properties=dict(device.properties),
                ))
        return changes
