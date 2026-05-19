import time, threading
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any, List
from .device_state import DeviceState, DeviceDetector
from .adb_manager import AdbManager
from .fastboot_manager import FastbootManager
from .capabilities import CapabilityDetector, DeviceCapabilities
from .partition_manager import PartitionManager, PartitionMap
from .logger import get_logger
logger = get_logger()

@dataclass(frozen=True)
class DeviceSnapshot:
    state: DeviceState
    serial: Optional[str]
    capabilities: DeviceCapabilities
    partitions: PartitionMap
    timestamp: float = field(default_factory=time.time)

class StateOrchestrator:
    def __init__(self, adb: AdbManager, fastboot: FastbootManager, detector: DeviceDetector,
                 capabilities: CapabilityDetector, partitions: PartitionManager,
                 event_callbacks: Optional[Dict[str,Callable]]=None):
        self.adb = adb
        self.fastboot = fastboot
        self.detector = detector
        self.capabilities = capabilities
        self.partitions = partitions
        self.events = event_callbacks or {}
        self._audit_log = []
        self._state_lock = threading.Lock()
        self._cached_snapshot = None
        self._snapshot_ttl = 2.0

    def snapshot(self, serial: Optional[str] = None, force_refresh=False) -> DeviceSnapshot:
        with self._state_lock:
            if not force_refresh and self._cached_snapshot:
                age = time.time() - self._cached_snapshot.timestamp
                if age < self._snapshot_ttl:
                    return self._cached_snapshot
        state, found_serial = self.detector.detect_state(serial)
        caps = self.capabilities.detect(state, found_serial)
        pmap = self.partitions.build_map(state, found_serial)
        snap = DeviceSnapshot(state, found_serial, caps, pmap)
        with self._state_lock:
            self._cached_snapshot = snap
        return snap

    def invalidate_snapshot(self):
        with self._state_lock:
            self._cached_snapshot = None

    def flash(self, serial: str, target: str, image_path: str, timeout=120) -> bool:
        with self._state_lock:
            logger.info(f"Flashing {target} on {serial}")
            res = self.fastboot._run(["flash", target, image_path], serial=serial, timeout=timeout)
            success = res.success
            self._audit_log.append({"timestamp": time.time(), "serial": serial, "target": target,
                                    "image": image_path, "success": success, "stderr": res.stderr})
            return success

    def safe_transition(self, target: DeviceState, serial: Optional[str]=None, timeout=30) -> str:
        # Simplified; full version would implement transitions
        snap = self.snapshot(serial=serial, force_refresh=True)
        cur = snap.state
        cur_serial = snap.serial or serial
        if cur == target:
            return cur_serial
        # For now, only support ADB -> FASTBOOT using adb reboot bootloader
        if target == DeviceState.FASTBOOT and cur == DeviceState.ADB:
            self.adb.reboot("bootloader", serial=cur_serial)
            time.sleep(3)
            self.invalidate_snapshot()
            return cur_serial
        raise Exception(f"Transition from {cur} to {target} not implemented in stub")
