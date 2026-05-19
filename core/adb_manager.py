"""
ADB Manager – Production Grade
- Device listing, shell commands, property management
- Persistent connection with retry
- Device recovery and state detection
"""

from typing import List, Tuple, Optional
import time

from .transport import Transport
from .command_result import CommandResult
from .logger import get_logger

logger = get_logger()


class AdbManager:
    def __init__(self, transport: Transport):
        self.transport = transport
        self._ensure_server()

    def _ensure_server(self):
        """Start ADB server if not running."""
        self.transport.adb(["start-server"], timeout=10)

    # ------------------------------------------------------------
    # Core ADB Operations
    # ------------------------------------------------------------
    def devices(self) -> List[Tuple[str, str]]:
        """Return list of (serial, state) for connected devices."""
        result = self.transport.adb(["devices"])
        devices = []
        for line in result.stdout.splitlines():
            # Skip daemon startup messages and header
            if line.startswith("* daemon") or not line.strip() or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                devices.append((parts[0], parts[1]))
        return devices

    def shell(self, command: str, serial: Optional[str] = None, timeout: int = 30) -> CommandResult:
        """Execute a shell command on the device."""
        args = []
        if serial:
            args += ["-s", serial]
        args += ["shell", command]
        return self.transport.adb(args, timeout=timeout)

    def get_prop(self, prop: str, serial: Optional[str] = None) -> Optional[str]:
        """Get a single Android system property."""
        res = self.shell(f"getprop {prop}", serial=serial, timeout=5)
        if res.success and res.stdout:
            return res.stdout.strip()
        return None

    def reboot(self, target: str = "", serial: Optional[str] = None) -> CommandResult:
        """Reboot device. Target can be 'bootloader', 'recovery', 'fastboot', or empty."""
        args = []
        if serial:
            args += ["-s", serial]
        args += ["reboot"]
        if target:
            args.append(target)
        return self.transport.adb(args, timeout=10)

    def pull(self, remote: str, local: str, serial: Optional[str] = None, timeout: int = 120) -> CommandResult:
        """Pull a file from device to local machine."""
        args = []
        if serial:
            args += ["-s", serial]
        args += ["pull", remote, local]
        return self.transport.adb(args, timeout=timeout)

    def push(self, local: str, remote: str, serial: Optional[str] = None, timeout: int = 120) -> CommandResult:
        """Push a file from local machine to device."""
        args = []
        if serial:
            args += ["-s", serial]
        args += ["push", local, remote]
        return self.transport.adb(args, timeout=timeout)

    def partition_exists(self, partition: str, serial: Optional[str] = None) -> bool:
        """Check if a partition exists on the device."""
        res = self.shell(f"ls /dev/block/by-name/{partition}", serial=serial, timeout=5)
        return res.success and "No such file" not in res.stderr

    # ------------------------------------------------------------
    # ADB Stability Layer - Persistent Connection & Recovery
    # ------------------------------------------------------------
    def persistent_connect(self, serial: str, max_retries: int = 3) -> bool:
        """Establish persistent ADB connection with retry."""
        for attempt in range(max_retries):
            result = self.shell("echo connected", serial=serial, timeout=5)
            if result.success and "connected" in result.stdout:
                logger.info(f"Persistent connection established to {serial}")
                return True
            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
        logger.error(f"Failed to establish persistent connection to {serial}")
        return False

    def wait_for_device(self, serial: str, timeout: int = 30) -> bool:
        """Wait for device to be ready."""
        start = time.time()
        while time.time() - start < timeout:
            result = self.shell("echo ready", serial=serial, timeout=5)
            if result.success and result.returncode == 0:
                logger.info(f"Device {serial} is ready")
                return True
            time.sleep(1)
        logger.error(f"Timeout waiting for device {serial}")
        return False

    def recover_device(self, serial: str) -> bool:
        """Attempt to recover offline or unauthorized device."""
        logger.info(f"Attempting to recover device {serial}")
        # Kill and restart ADB server
        self.transport.adb(["kill-server"], timeout=5)
        time.sleep(1)
        self._ensure_server()
        time.sleep(2)
        return self.persistent_connect(serial)

    def get_device_state(self, serial: str) -> str:
        """Get detailed device state (device, recovery, sideload, offline, unauthorized)."""
        devices = self.devices()
        for s, state in devices:
            if s == serial:
                return state
        return "disconnected"