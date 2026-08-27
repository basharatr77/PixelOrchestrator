from app.core.module_contract import DeviceState
from app.core.transport_factory import TransportFactory


class TransportResolver:
    @staticmethod
    def resolve(device):
        if device is None:
            raise ValueError("device is required")

        if device.state is DeviceState.ADB:
            mode = "ADB"
        elif device.state is DeviceState.FASTBOOT:
            mode = "FASTBOOT"
        else:
            raise ValueError(
                f"Unsupported device state: {device.state}"
            )

        return TransportFactory.create(
            serial=device.serial,
            mode=mode,
        )
