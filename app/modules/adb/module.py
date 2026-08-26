"""ADB Module V1 for PixelOrchestrator.

Provides Android Debug Bridge capabilities through the common
PixelOrchestrator module contract.
"""

import subprocess

from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    Device,
    DeviceState,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)


class ADBModule(ModuleContract):
    """ADB transport and device operations."""

    manifest = ModuleManifest(
        id="adb",
        name="ADB",
        version="1.0.0",
        module_type=ModuleType.ADB,
        description="Android Debug Bridge device management and operations.",
        capabilities=(
            Capability(
                id="adb_detection",
                name="ADB Device Detection",
                description="Detect devices available through ADB.",
            ),
            Capability(
                id="adb_information",
                name="ADB Device Information",
                description="Read device information through ADB.",
            ),
            Capability(
                id="adb_shell",
                name="ADB Shell",
                description="Execute ADB shell commands.",
            ),
        ),
        actions=(
            Action(
                id="refresh_devices",
                name="Refresh ADB Devices",
                description="Detect currently connected ADB devices.",
                capability_id="adb_detection",
                requires_device=False,
            ),
            Action(
                id="device_info",
                name="ADB Device Information",
                description="Read information from an ADB device.",
                capability_id="adb_information",
                requires_device=True,
            ),
            Action(
                id="shell",
                name="ADB Shell",
                description="Execute an ADB shell command.",
                capability_id="adb_shell",
                requires_device=True,
            ),
        ),
    )

    def detect(self) -> list[Device]:
        """Detect devices currently visible to ADB."""

        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            return []

        devices = []

        for line in result.stdout.splitlines()[1:]:
            line = line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) < 2:
                continue

            serial = parts[0]
            status = parts[1]

            if status == "device":
                state = DeviceState.ADB
            elif status == "offline":
                state = DeviceState.CONNECTED
            else:
                state = DeviceState.UNKNOWN

            devices.append(
                Device(
                    device_id=f"adb:{serial}",
                    module_type=ModuleType.ADB,
                    state=state,
                    serial=serial,
                    transport="adb",
                )
            )

        return devices

    def execute(
        self,
        action_id: str,
        device: Device | None = None,
        **kwargs,
    ) -> ActionResult:
        """Execute an ADB module action."""

        if action_id == "refresh_devices":
            devices = self.detect()

            return ActionResult(
                success=True,
                message=f"ADB detection completed: {len(devices)} device(s) found.",
                data={
                    "devices": [
                        {
                            "device_id": item.device_id,
                            "serial": item.serial,
                            "state": item.state.value,
                            "transport": item.transport,
                        }
                        for item in devices
                    ]
                },
            )

        if action_id == "device_info":
            if device is None:
                return ActionResult(
                    success=False,
                    message="An ADB device is required.",
                    error_code="DEVICE_REQUIRED",
                )

            if not device.serial:
                return ActionResult(
                    success=False,
                    message="ADB device serial is required.",
                    error_code="SERIAL_REQUIRED",
                )

            try:
                result = subprocess.run(
                    [
                        "adb",
                        "-s",
                        device.serial,
                        "shell",
                        "getprop",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
            except FileNotFoundError:
                return ActionResult(
                    success=False,
                    message="ADB executable was not found.",
                    error_code="ADB_NOT_FOUND",
                )
            except subprocess.SubprocessError as exc:
                return ActionResult(
                    success=False,
                    message=f"ADB command failed: {exc}",
                    error_code="ADB_EXECUTION_ERROR",
                )

            if result.returncode != 0:
                return ActionResult(
                    success=False,
                    message=result.stderr.strip() or "ADB device information failed.",
                    error_code="ADB_COMMAND_FAILED",
                )

            return ActionResult(
                success=True,
                message="ADB device information retrieved.",
                data={
                    "serial": device.serial,
                    "properties": result.stdout,
                },
            )

        if action_id == "shell":
            if device is None:
                return ActionResult(
                    success=False,
                    message="An ADB device is required.",
                    error_code="DEVICE_REQUIRED",
                )

            if not device.serial:
                return ActionResult(
                    success=False,
                    message="ADB device serial is required.",
                    error_code="SERIAL_REQUIRED",
                )

            command = kwargs.get("command")

            if not command or not str(command).strip():
                return ActionResult(
                    success=False,
                    message="A shell command is required.",
                    error_code="COMMAND_REQUIRED",
                )

            try:
                result = subprocess.run(
                    [
                        "adb",
                        "-s",
                        device.serial,
                        "shell",
                        str(command),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
            except FileNotFoundError:
                return ActionResult(
                    success=False,
                    message="ADB executable was not found.",
                    error_code="ADB_NOT_FOUND",
                )
            except subprocess.SubprocessError as exc:
                return ActionResult(
                    success=False,
                    message=f"ADB command failed: {exc}",
                    error_code="ADB_EXECUTION_ERROR",
                )

            return ActionResult(
                success=result.returncode == 0,
                message=(
                    result.stdout.strip()
                    if result.returncode == 0
                    else result.stderr.strip() or "ADB shell command failed."
                ),
                data={
                    "serial": device.serial,
                    "command": str(command),
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
                error_code=(
                    None if result.returncode == 0 else "ADB_COMMAND_FAILED"
                ),
            )

        return ActionResult(
            success=False,
            message=f"Unknown action: {action_id}",
            error_code="UNKNOWN_ACTION",
        )
