import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .adb_manager import AdbManager
from .fastboot_manager import FastbootManager
from .device_state import DeviceState
from .logger import get_logger
logger = get_logger()

@dataclass
class Partition:
    name: str
    slot: Optional[str] = None
    path: Optional[str] = None
    size: Optional[str] = None
    type: Optional[str] = None
    source: str = "unknown"
    def full_name(self):
        return f"{self.name}_{self.slot}" if self.slot else self.name
    def is_logical(self):
        return self.type == "logical"

@dataclass
class PartitionMap:
    partitions: Dict[str, Partition] = field(default_factory=dict)
    def add(self, p):
        self.partitions[p.full_name()] = p
    def get(self, full_name):
        return self.partitions.get(full_name)
    def get_by_logical(self, name, slot=None):
        if slot:
            return self.get(f"{name}_{slot}")
        for s in (None, "a", "b"):
            cand = self.get(f"{name}_{s}" if s else name)
            if cand:
                return cand
        return None
    def all(self):
        return list(self.partitions.values())

class PartitionManager:
    def __init__(self, adb: AdbManager, fastboot: FastbootManager):
        self.adb = adb
        self.fastboot = fastboot

    def build_map(self, state: DeviceState, serial: Optional[str] = None) -> PartitionMap:
        pmap = PartitionMap()
        if state == DeviceState.ADB:
            res = self.adb.shell("ls -l /dev/block/by-name", serial=serial, timeout=10)
            if res.success:
                for line in res.stdout.splitlines():
                    m = re.match(r"(\S+)\s+->\s+(.+)", line.strip())
                    if m:
                        name, path = m.groups()
                        base, slot = self._split_slot(name)
                        pmap.add(Partition(name=base, slot=slot, path=path.strip(), source="adb"))
        elif state in (DeviceState.FASTBOOT, DeviceState.FASTBOOTD):
            v = self.fastboot.get_all_vars(serial=serial)
            src = "fastbootd" if state == DeviceState.FASTBOOTD else "fastboot"
            for k, val in v.items():
                if k.startswith("partition-size:"):
                    raw = k.split(":", 1)[1]
                    base, slot = self._split_slot(raw)
                    pmap.add(Partition(name=base, slot=slot, size=val, source=src))
                elif k.startswith("partition-type:"):
                    raw = k.split(":", 1)[1]
                    base, slot = self._split_slot(raw)
                    part = pmap.get(f"{base}_{slot}" if slot else base)
                    if part:
                        part.type = val
                    else:
                        pmap.add(Partition(name=base, slot=slot, type=val, source=src))
        return pmap

    @staticmethod
    def _split_slot(full: str) -> Tuple[str, Optional[str]]:
        m = re.match(r"(.+)_([ab])$", full)
        return (m.group(1), m.group(2)) if m else (full, None)
