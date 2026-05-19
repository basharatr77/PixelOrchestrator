import threading
from typing import List, Dict, Any
from core.flashing_engine import FlashingEngine
from core.state_orchestrator import StateOrchestrator
from core.distributed.master.scheduler import Scheduler
from core.logger import get_logger
logger = get_logger()

class MultiDeviceFlasher:
    def __init__(self, orchestrator: StateOrchestrator, scheduler: Scheduler):
        self.orchestrator = orchestrator
        self.scheduler = scheduler
        self.results = []

    def flash_all_devices(self, image_path: str, partition: str = "boot") -> Dict[str, Any]:
        """Flash the same image to all connected devices (ADB or fastboot)."""
        # Get all devices (simplified – you would get from orchestrator snapshot per serial)
        # For this stub, we assume we have a list of serials
        serials = self._get_all_serials()
        if not serials:
            return {"error": "No devices found"}
        threads = []
        results = {}
        for serial in serials:
            t = threading.Thread(target=self._flash_one, args=(serial, partition, image_path, results))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        return results

    def _get_all_serials(self):
        """Retrieve serials from ADB + fastboot."""
        adb_devices = self.orchestrator.adb.devices()
        fastboot_devices = self.orchestrator.fastboot.devices()
        serials = [s for s,_ in adb_devices] + list(fastboot_devices)
        return serials

    def _flash_one(self, serial: str, partition: str, image_path: str, results: dict):
        try:
            # Ensure device in fastboot
            snap = self.orchestrator.snapshot(serial=serial)
            if snap.state not in ("fastboot", "fastbootd"):
                self.orchestrator.safe_transition("fastboot", serial=serial)
            # Flash using existing flasher engine
            from core.flashing_engine import FlashingEngine
            flasher = FlashingEngine(self.orchestrator)
            op = flasher.flash_partition(partition, image_path)
            results[serial] = {"success": op.success, "message": op.message}
        except Exception as e:
            results[serial] = {"success": False, "error": str(e)}
