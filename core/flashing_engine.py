"""
Flashing Engine – with transactional backup & rollback
"""

import os
import tempfile
import time
import hashlib
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass

from .state_orchestrator import StateOrchestrator
from .device_state import DeviceState
from .logger import get_logger, log_event
from .exceptions import DeviceStateError, ImageFileError

logger = get_logger()

@dataclass
class FlashOperation:
    partition: str
    image_path: str
    slot: Optional[str]
    success: bool
    message: str
    duration_sec: float = 0
    verification_passed: bool = False
    rollback_performed: bool = False

class FlashingEngine:
    def __init__(self, orchestrator: StateOrchestrator):
        self.orchestrator = orchestrator
        self.dry_run = False
        self._verify_after_flash = True
        self._max_retries = 2
        self._retry_delay = 2
        # Backup engine will be lazily imported to avoid circular imports
        self._backup_engine = None

    def _get_backup_engine(self):
        if self._backup_engine is None:
            from .backup_engine import BackupEngine
            self._backup_engine = BackupEngine(self.orchestrator)
        return self._backup_engine

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------
    def flash_partition(
        self,
        partition_name: str,
        image_path: str,
        slot: Optional[str] = None,
        force: bool = False,
        transactional: bool = True,
        progress_callback: Optional[Callable[[int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> FlashOperation:
        """
        Flash a single partition with optional transactional backup & rollback.
        If transactional=True, it backs up the current partition before flashing,
        and automatically restores if the flash fails.
        """
        import time
        start_time = time.time()
        rollback_done = False

        if log_callback:
            log_callback(f"Starting flash of {partition_name} from {image_path}")

        # 1. Validate image file
        if not self._validate_image(image_path):
            return FlashOperation(
                partition_name, image_path, slot, False,
                "Image file not found or invalid", 0, False
            )

        # 2. Dry run check
        if self.dry_run:
            if log_callback:
                log_callback(f"[DRY RUN] Would flash {partition_name}")
            return FlashOperation(
                partition_name, image_path, slot, True,
                "Dry run - no action", 0, False
            )

        # 3. Get device snapshot and resolve partition
        snap = self.orchestrator.snapshot()
        serial = snap.serial
        if not serial:
            return FlashOperation(
                partition_name, image_path, slot, False,
                "No device connected", 0, False
            )

        # 4. Ensure device in correct state (fastboot/fastbootd)
        target_state = self._get_required_state(snap, partition_name, slot)
        if snap.state != target_state:
            if log_callback:
                log_callback(f"Transitioning from {snap.state.value} to {target_state.value}")
            try:
                self.orchestrator.safe_transition(target_state, serial=serial)
                snap = self.orchestrator.snapshot(force_refresh=True)
            except Exception as e:
                return FlashOperation(
                    partition_name, image_path, slot, False,
                    f"State transition failed: {e}", 0, False
                )

        # 5. Resolve partition with slot
        part = snap.partitions.get_by_logical(partition_name, slot)
        if not part:
            return FlashOperation(
                partition_name, image_path, slot, False,
                f"Partition {partition_name} not found", 0, False
            )
        target = part.full_name()
        if log_callback:
            log_callback(f"Target partition: {target}")

        # 6. Transactional backup (if enabled)
        backup_path = None
        if transactional and self._is_critical_partition(partition_name):
            if log_callback:
                log_callback(f"Creating backup of {target} before flashing...")
            backup_path = self._backup_partition(serial, target, log_callback)
            if not backup_path:
                return FlashOperation(
                    partition_name, image_path, slot, False,
                    "Failed to create backup before flash", 0, False
                )
            if log_callback:
                log_callback(f"Backup saved to {backup_path}")

        # 7. Flash with retry logic
        success = False
        last_error = ""
        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                if log_callback:
                    log_callback(f"Retry attempt {attempt}/{self._max_retries}")
                time.sleep(self._retry_delay)

            result = self.orchestrator.flash(serial, target, image_path, timeout=120)
            if result:
                if self._verify_after_flash:
                    verification = self._verify_flash(serial, target, image_path)
                    if verification:
                        success = True
                        break
                    else:
                        last_error = "Verification failed"
                else:
                    success = True
                    break
            else:
                last_error = "Flash command failed"

            if progress_callback:
                progress_callback(int((attempt + 1) / (self._max_retries + 1) * 100))

        duration = time.time() - start_time

        # 8. If flash failed and we have a backup, restore it
        if not success and backup_path:
            if log_callback:
                log_callback(f"Flash failed. Rolling back from {backup_path}...")
            restore_result = self._restore_partition(serial, target, backup_path, log_callback)
            if restore_result:
                rollback_done = True
                if log_callback:
                    log_callback("Rollback successful – device restored to previous state.")
            else:
                if log_callback:
                    log_callback("CRITICAL: Rollback failed! Device may be in inconsistent state.")

        if success:
            if log_callback:
                log_callback(f"Successfully flashed {target} in {duration:.2f}s")
            # Cleanup backup if it exists
            if backup_path:
                self._cleanup_backup(backup_path)
            return FlashOperation(
                partition_name, image_path, slot, True,
                f"Flashed successfully in {duration:.2f}s", duration, True, rollback_done
            )
        else:
            msg = f"Failed after {self._max_retries} retries: {last_error}"
            if rollback_done:
                msg += " (Rollback performed)"
            return FlashOperation(
                partition_name, image_path, slot, False,
                msg, duration, False, rollback_done
            )

    def flash_multiple(
        self,
        images: Dict[str, str],
        slot: Optional[str] = None,
        transactional: bool = True,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> List[FlashOperation]:
        """Flash multiple partitions in sequence."""
        results = []
        for partition, path in images.items():
            result = self.flash_partition(partition, path, slot, transactional=transactional, log_callback=log_callback)
            results.append(result)
            if not result.success:
                if log_callback:
                    log_callback(f"Stopping due to failure on {partition}")
                break
        return results

    # ------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------
    def _validate_image(self, image_path: str) -> bool:
        if not os.path.isfile(image_path):
            return False
        if os.path.getsize(image_path) == 0:
            return False
        return True

    def _get_required_state(self, snap, partition_name: str, slot: Optional[str]) -> DeviceState:
        part = snap.partitions.get_by_logical(partition_name, slot)
        if part and part.is_logical():
            return DeviceState.FASTBOOTD
        return DeviceState.FASTBOOT

    def _verify_flash(self, serial: str, target: str, image_path: str) -> bool:
        """Verify flashed partition by reading back and comparing hash."""
        import tempfile
        temp_dir = tempfile.gettempdir()
        remote_path = f"/sdcard/verify_{target}.img"
        local_path = os.path.join(temp_dir, f"verify_{target}.img")

        try:
            self.orchestrator.adb.shell(f"dd if=/dev/block/by-name/{target} of={remote_path}", serial=serial)
            self.orchestrator.adb.pull(remote_path, local_path, serial=serial)
            self.orchestrator.adb.shell(f"rm {remote_path}", serial=serial)

            local_hash = self._compute_hash(image_path)
            remote_hash = self._compute_hash(local_path)

            if local_hash == remote_hash:
                logger.info(f"Verification passed for {target}")
                return True
            else:
                logger.error(f"Verification failed for {target}")
                return False
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)

    def _compute_hash(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _is_critical_partition(self, partition_name: str) -> bool:
        """Decide which partitions should be backed up before flash."""
        critical = ["boot", "boot_a", "boot_b", "init_boot", "vbmeta", "system", "vendor", "dtbo"]
        return partition_name in critical

    def _backup_partition(self, serial: str, target: str, log_callback=None) -> Optional[str]:
        """Backup a partition using existing BackupEngine."""
        try:
            backup_engine = self._get_backup_engine()
            # Create a temporary directory for backup
            temp_dir = tempfile.mkdtemp(prefix="px_flash_backup_")
            # The backup engine's backup_partitions expects a list of logical names
            # We need the logical name (without slot suffix)
            logical_name = target.split('_')[0]  # e.g., "boot" from "boot_a"
            # Call backup engine
            results = backup_engine.backup_partitions(temp_dir, [logical_name])
            if results and len(results) > 0:
                backup_path = results[0].image_path
                log_event(serial, "backup", "INFO", f"Backup created: {backup_path}")
                return backup_path
            else:
                log_event(serial, "backup", "ERROR", "Backup engine returned no result")
                return None
        except Exception as e:
            log_event(serial, "backup", "ERROR", str(e))
            if log_callback:
                log_callback(f"Backup failed: {e}")
            return None

    def _restore_partition(self, serial: str, target: str, backup_path: str, log_callback=None) -> bool:
        """Restore a partition from a backup image using fastboot flash."""
        try:
            # Ensure device is in fastboot mode
            snap = self.orchestrator.snapshot()
            if snap.state not in (DeviceState.FASTBOOT, DeviceState.FASTBOOTD):
                self.orchestrator.safe_transition(DeviceState.FASTBOOT, serial=serial)
                time.sleep(1)
            # Flash the backup image
            result = self.orchestrator.flash(serial, target, backup_path, timeout=120)
            if result:
                log_event(serial, "restore", "INFO", f"Restored {target} from backup")
                return True
            else:
                log_event(serial, "restore", "ERROR", f"Failed to restore {target}")
                return False
        except Exception as e:
            log_event(serial, "restore", "ERROR", str(e))
            if log_callback:
                log_callback(f"Restore failed: {e}")
            return False

    def _cleanup_backup(self, backup_path: str):
        """Delete the backup directory and file."""
        try:
            directory = os.path.dirname(backup_path)
            if os.path.exists(directory):
                import shutil
                shutil.rmtree(directory)
        except Exception:
            pass

    def set_dry_run(self, enabled: bool):
        self.dry_run = enabled

    def enable_verification(self, enabled: bool):
        self._verify_after_flash = enabled