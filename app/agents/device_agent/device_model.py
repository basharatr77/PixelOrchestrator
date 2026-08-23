from dataclasses import asdict, dataclass


@dataclass
class Device:
    serial: str
    mode: str
    brand: str = ""
    model: str = ""
    android_version: str = ""

    def to_dict(self):
        return asdict(self)
