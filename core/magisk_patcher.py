import os, subprocess, tempfile, shutil
from typing import Optional
from core.state_orchestrator import StateOrchestrator
from core.flashing_engine import FlashingEngine
from core.logger import get_logger
logger = get_logger()

class MagiskPatcher:
    def __init__(self, orchestrator: StateOrchestrator, flasher: FlashingEngine):
        self.orchestrator = orchestrator
        self.flasher = flasher
        self.magiskboot_path = self._find_magiskboot()
        self.dry_run = False

    def _find_magiskboot(self):
        # Try bundled, then PATH
        bundled = os.path.join(os.getcwd(), "bin", "magiskboot")
        if os.name == 'nt':
            bundled += ".exe"
        if os.path.isfile(bundled):
            return bundled
        which = shutil.which("magiskboot")
        if which:
            return which
        raise Exception("magiskboot not found. Place it in ./bin/ or add to PATH")

    def patch_and_flash(self, stock_img: Optional[str] = None, slot: Optional[str] = None) -> bool:
        """Patch current boot image (or given stock image) and flash it."""
        snap = self.orchestrator.snapshot()
        if snap.state != "adb":
            raise Exception("Device must be in ADB mode to pull boot image")
        serial = snap.serial
        # Determine boot partition name (boot or init_boot)
        caps = snap.capabilities
        boot_part_name = "init_boot" if caps.init_boot else "boot"
        part = snap.partitions.get_by_logical(boot_part_name, slot)
        if not part:
            raise Exception(f"{boot_part_name} partition not found")
        target = part.full_name()
        # Pull current image if not provided
        if not stock_img:
            local_img = os.path.join(tempfile.gettempdir(), f"{target}.img")
            device_temp = f"/sdcard/{target}.img"
            block_path = part.path or f"/dev/block/by-name/{target}"
            self.orchestrator.adb.shell(f"dd if={block_path} of={device_temp}", serial=serial)
            self.orchestrator.adb.pull(device_temp, local_img, serial=serial)
            self.orchestrator.adb.shell(f"rm {device_temp}", serial=serial)
            stock_img = local_img
        # Patch using magiskboot
        patched_img = stock_img.replace(".img", "_patched.img")
        if self.dry_run:
            logger.info(f"Dry run: would patch {stock_img} -> {patched_img}")
        else:
            cmd = [self.magiskboot_path, "patch", stock_img, patched_img]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Magisk patching failed: {result.stderr}")
            if not os.path.isfile(patched_img):
                raise Exception("Patched image not created")
        # Flash patched image
        success = self.flasher.flash_partition(boot_part_name, patched_img, slot=slot).success
        return success
