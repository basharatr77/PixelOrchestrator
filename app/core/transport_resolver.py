from app.core.transport_factory import TransportFactory


class TransportResolver:
    @staticmethod
    def resolve(device):
        if device is None:
            raise ValueError("device is required")

        return TransportFactory.create(
            serial=device.serial,
            mode=device.mode,
        )
