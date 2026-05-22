"""
Enterprise Device State Machine – transitions library based
"""

from enum import Enum
from transitions import Machine
from typing import Optional, Callable, Any
import threading

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
        self._lock = threading.Lock()
        self._on_state_change = on_state_change

        self.machine = Machine(
            model=self,
            states=[s.value for s in DeviceState],
            initial=DeviceState.DISCONNECTED.value,
            transitions=[
                { 'trigger': 'detect_usb', 'source': 'disconnected', 'dest': 'usb' },
                { 'trigger': 'adb_ready',   'source': 'usb', 'dest': 'adb' },
                { 'trigger': 'adb_ready',   'source': 'recovery', 'dest': 'adb' },
                { 'trigger': 'recovery_mode','source': 'adb', 'dest': 'recovery' },
                { 'trigger': 'fastboot_mode','source': 'adb', 'dest': 'fastboot' },
                { 'trigger': 'fastboot_mode','source': 'usb', 'dest': 'fastboot' },
                { 'trigger': 'edl_mode',    'source': 'fastboot', 'dest': 'edl' },
                { 'trigger': 'sideload_mode','source': 'adb', 'dest': 'sideload' },
                { 'trigger': 'disconnect',  'source': '*', 'dest': 'disconnected' },
            ],
            send_event=True,
            after_state_change='_after_change'
        )

    def _after_change(self, event):
        if self._on_state_change:
            self._on_state_change(self.serial, event.state, event.transition)

    def safe_transition(self, target: DeviceState) -> bool:
        with self._lock:
            try:
                for t in self.machine.get_triggers(self.state):
                    if target.value == self.machine.get_state(t).name:
                        getattr(self, t)()
                        return True
                return False
            except Exception as e:
                print(f"Invalid transition: {self.state} -> {target.value}")
                return False
