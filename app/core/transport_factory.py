from app.core.adb_transport import ADBTransport
from app.core.fastboot_transport import FastbootTransport


class TransportFactory:
    @staticmethod
    def create(serial, mode):
        if not serial:
            raise ValueError("serial is required")

        if mode == "ADB":
            return ADBTransport(serial)

        if mode == "FASTBOOT":
            return FastbootTransport(serial)

        raise ValueError(
            f"Unsupported transport mode: {mode}"
        )
