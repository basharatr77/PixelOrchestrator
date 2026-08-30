from app.core.module_contract import Device, DeviceState


class DeviceStateMachine:
    """Validate and apply canonical device lifecycle transitions."""

    VALID_TRANSITIONS = {
        DeviceState.UNKNOWN: {
            DeviceState.DISCONNECTED,
            DeviceState.ADB,
            DeviceState.RECOVERY,
            DeviceState.SIDELOAD,
            DeviceState.FASTBOOT,
            DeviceState.FASTBOOTD,
            DeviceState.EDL,
        },
        DeviceState.DISCONNECTED: {
            DeviceState.ADB,
            DeviceState.RECOVERY,
            DeviceState.SIDELOAD,
            DeviceState.FASTBOOT,
            DeviceState.FASTBOOTD,
            DeviceState.EDL,
        },
        DeviceState.ADB: {
            DeviceState.DISCONNECTED,
            DeviceState.RECOVERY,
            DeviceState.SIDELOAD,
            DeviceState.FASTBOOT,
            DeviceState.FASTBOOTD,
        },
        DeviceState.RECOVERY: {
            DeviceState.DISCONNECTED,
            DeviceState.ADB,
            DeviceState.SIDELOAD,
            DeviceState.FASTBOOT,
        },
        DeviceState.SIDELOAD: {
            DeviceState.DISCONNECTED,
            DeviceState.ADB,
            DeviceState.RECOVERY,
        },
        DeviceState.FASTBOOT: {
            DeviceState.DISCONNECTED,
            DeviceState.ADB,
            DeviceState.RECOVERY,
            DeviceState.FASTBOOTD,
        },
        DeviceState.FASTBOOTD: {
            DeviceState.DISCONNECTED,
            DeviceState.ADB,
            DeviceState.RECOVERY,
            DeviceState.FASTBOOT,
        },
        DeviceState.EDL: {
            DeviceState.DISCONNECTED,
        },
    }

    @classmethod
    def transition(
        cls,
        device: Device,
        target: DeviceState,
    ) -> Device:
        if not isinstance(device, Device):
            raise TypeError("device must be a canonical Device")

        if not isinstance(target, DeviceState):
            raise TypeError("target must be a DeviceState")

        current = device.state

        if target not in cls.VALID_TRANSITIONS.get(current, set()):
            raise ValueError(
                f"Invalid device state transition: "
                f"{current.value} -> {target.value}"
            )

        device.state = target
        return device
