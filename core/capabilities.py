from dataclasses import dataclass, field
from typing import Dict, Optional
from .device_state import DeviceState
from .adb_manager import AdbManager
from .fastboot_manager import FastbootManager
from .logger import get_logger
logger = get_logger()

@dataclass
class DeviceCapabilities:
    ab_slots: bool = False
    dynamic_partitions: bool = False
    fastbootd_supported: bool = False
    tensor: bool = False
    init_boot: bool = False
    codename: Optional[str] = None
    android_version: Optional[int] = None
    raw_vars: Dict[str, str] = field(default_factory=dict)

class CapabilityDetector:
    def __init__(self, adb: AdbManager, fastboot: FastbootManager):
        self.adb = adb
        self.fastboot = fastboot
        self._cache: Dict[str, DeviceCapabilities] = {}

    def detect(self, state: DeviceState, serial: Optional[str]) -> DeviceCapabilities:
        if not serial:
            return DeviceCapabilities()
        if serial in self._cache:
            return self._cache[serial]
        caps = DeviceCapabilities()
        if state in (DeviceState.FASTBOOT, DeviceState.FASTBOOTD):
            v = self.fastboot.get_all_vars(serial=serial)
            caps.raw_vars = v
            slot_count = v.get("slot-count", "0")
            if slot_count.isdigit() and int(slot_count) > 0:
                caps.ab_slots = True
            if v.get("has-logical:system") == "yes" or v.get("is-logical:system") == "yes":
                caps.dynamic_partitions = True
            caps.fastbootd_supported = (state == DeviceState.FASTBOOTD) or (v.get("is-userspace") == "yes")
            caps.codename = v.get("product")
            if caps.codename:
                caps.tensor = caps.codename in {"panther","cheetah","lynx","oriole","raven","bluejay","husky","shiba","felix"}
            caps.init_boot = self.fastboot.getvar("partition-type:init_boot", serial=serial) is not None
        elif state == DeviceState.ADB:
            caps.codename = self.adb.get_prop("ro.product.device", serial)
            ver = self.adb.get_prop("ro.build.version.sdk", serial)
            if ver and ver.isdigit():
                caps.android_version = int(ver)
            caps.init_boot = self.adb.partition_exists("init_boot", serial)
            caps.ab_slots = bool(self.adb.get_prop("ro.boot.slot_suffix", serial))
            if caps.codename:
                caps.tensor = caps.codename in {"panther","cheetah","lynx","oriole","raven","bluejay","husky","shiba","felix"}
            caps.dynamic_partitions = self.adb.partition_exists("super", serial)
        self._cache[serial] = caps
        return caps
