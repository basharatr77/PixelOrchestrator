"""
Restore Engine – Production Grade
- Manifest-based restore
- SHA256 verification before flashing
- Slot-aware restore
"""

import os
import json
import hashlib
from typing import List, Optional
from dataclasses import dataclass

from .state_orchestrator import StateOrchestrator
from .device_state import DeviceState
from .logger import get_logger

logger = get_logger()

@dataclass
class RestoreResult:
    device_serial: str
    restored: List[str]
    failed: List[str]

class RestoreEngine:
    def __init__(self, orchestrator: StateOrchestrator):
        self.orchestrator = orchestrator
        self.dry_run = False
        self._verify_before_restore = True

    def restore_from_manifest(
        self,
        manifest_path: str,
        slot: Optional[str] = None,
        verify: bool = True
    ) -> RestoreResult:
        """
        Restore partitions from backup manifest.
        """
        if not os.path.isfile(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path, "r") as f:
            data = json.load(f)

        snap = self.orchestrator.snapshot()
        serial = snap.serial
        if not serial:
            raise Exception("No device connected")

        # Ensure device is in flashable state
        if snap.state not in (DeviceState.FASTBOOT, DeviceState.FASTBOOTD):
            self.orchestrator.safe_transition(DeviceState.FASTBOOT, serial=serial)
            snap = self.orchestrator.snapshot(force_refresh=True)

        restored = []
        failed = []
        manifest_dir = os.path.dirname(manifest_path)

        for item in data.get("items", []):
            full_name = item.get("full_name", "")
            expected_sha = item.get("sha256", "")
            image_file = item.get("image_path", "")
            
            # Resolve image path (absolute or relative to manifest)
            if not os.path.isabs(image_file):
                image_file = os.path.join(manifest_dir, os.path.basename(image_file))
            
            if not os.path.isfile(image_file):
                logger.error(f"Image not found: {image_file}")
                failed.append(full_name)
                continue

            # Verify SHA256
            if verify and self._verify_before_restore:
                actual_sha = self._compute_sha256(image_file)
                if actual_sha != expected_sha:
                    logger.error(f"SHA256 mismatch for {full_name}")
                    failed.append(full_name)
                    continue

            # Resolve partition
            part = snap.partitions.get_by_logical(full_name.split("_")[0], slot)
            if not part:
                logger.error(f"Partition not found: {full_name}")
                failed.append(full_name)
                continue

            target = part.full_name()
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would restore {target}")
                restored.append(full_name)
                continue

            # Flash the image
            success = self.orchestrator.flash(serial, target, image_file)
            if success:
                restored.append(full_name)
                logger.info(f"Restored {target}")
            else:
                failed.append(full_name)
                logger.error(f"Failed to restore {target}")

        return RestoreResult(serial, restored, failed)

    def _compute_sha256(self, file_path: str) -> str:
        """Compute SHA256 hash."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                sha256.update(chunk)
        return sha256.hexdigest()

    def set_dry_run(self, enabled: bool):
        self.dry_run = enabled