"""
Enterprise Device State Machine using transitions library.
"""

from enum import Enum
from transitions import Machine
from typing import Optional, Callable

class DeviceState(Enum):
    DISCONNECTED = "disconnected"
    USB = "usb"
    ADB = "adb"
    RECOVERY = "recovery"
    FASTBOOT = "fastboot"
    SIDELOAD = "sideload"
    EDL = "edl"
    OFFLINE = "offline"

class DeviceStateMachine:
    def __init__(self, serial: str, on_state_change: Optional[Callable] = None):
        self.serial = serial
        self.state = DeviceState.DISCONNECTED
        self._on_state_change = on_state_change

        self.machine = Machine(
            model=self,
            states=[s.value for s in DeviceState],
            initial=DeviceState.DISCONNECTED.value,
            transitions=[
                { 'trigger': 'detect_usb',    'source': 'disconnected', 'dest': 'usb' },
                { 'trigger': 'adb_ready',     'source': 'usb', 'dest': 'adb' },
                { 'trigger': 'adb_ready',     'source': 'recovery', 'dest': 'adb' },
                { 'trigger': 'recovery_mode', 'source': 'adb', 'dest': 'recovery' },
                { 'trigger': 'fastboot_mode', 'source': 'adb', 'dest': 'fastboot' },
                { 'trigger': 'fastboot_mode', 'source': 'usb', 'dest': 'fastboot' },
                { 'trigger': 'edl_mode',      'source': 'fastboot', 'dest': 'edl' },
                { 'trigger': 'sideload_mode', 'source': 'adb', 'dest': 'sideload' },
                { 'trigger': 'disconnect',    'source': '*', 'dest': 'disconnected' },
                { 'trigger': 'offline',       'source': '*', 'dest': 'offline' },
            ],
            send_event=True,
            after_state_change='_after_change'
        )

    def _after_change(self, event):
        if self._on_state_change:
            self._on_state_change(self.serial, event.state.name, event.transition.name)

    def safe_transition(self, target: DeviceState) -> bool:
        """Try to transition to target state using appropriate trigger."""
        # Map target state to the trigger that leads to it
        target_map = {
            DeviceState.ADB: "adb_ready",
            DeviceState.FASTBOOT: "fastboot_mode",
            DeviceState.EDL: "edl_mode",
            DeviceState.RECOVERY: "recovery_mode",
            DeviceState.SIDELOAD: "sideload_mode",
            DeviceState.USB: "detect_usb",
            DeviceState.DISCONNECTED: "disconnect",
            DeviceState.OFFLINE: "offline",
        }
        trigger_name = target_map.get(target)
        if not trigger_name:
            return False

        # Get the trigger method and call it if allowed by current state
        if hasattr(self, trigger_name):
            try:
                getattr(self, trigger_name)()
                return True
            except Exception:
                return False
        return False