from dataclasses import dataclass

@dataclass
class Device:
    serial: str
    mode: str
    brand: str = ""
    model: str = ""
    android_version: str = ""
