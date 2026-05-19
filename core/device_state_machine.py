"""
Device State Machine – Deterministic State Management for Device Orchestration
"""

from enum import Enum
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import threading
import time


class DeviceState(Enum):
    """Deterministic device states for orchestration."""
    DISCONNECTED = "disconnected"
    DETECTING = "detecting"
    ADB = "adb"
    UNAUTHORIZED = "unauthorized"
    RECOVERY = "recovery"
    SIDELOAD = "sideload"
    FASTBOOT = "fastboot"
    FASTBOOTD = "fastbootd"
    EDL = "edl"
    BROM = "brom"
    FLASHING = "flashing"
    REBOOTING = "rebooting"
    BUSY = "busy"
    FAILED = "failed"
    
    @classmethod
    def from_string(cls, value: str) -> "DeviceState":
        """Convert string to DeviceState enum."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.DISCONNECTED


class StateTransition:
    """Allowed transitions between states."""
    
    ALLOWED = {
        DeviceState.DISCONNECTED: [DeviceState.DETECTING, DeviceState.ADB, DeviceState.FASTBOOT, DeviceState.EDL],
        DeviceState.DETECTING: [DeviceState.DISCONNECTED, DeviceState.ADB, DeviceState.FASTBOOT, DeviceState.EDL],
        DeviceState.ADB: [DeviceState.DISCONNECTED, DeviceState.RECOVERY, DeviceState.SIDELOAD, 
                         DeviceState.FASTBOOT, DeviceState.FLASHING, DeviceState.REBOOTING, DeviceState.BUSY],
        DeviceState.UNAUTHORIZED: [DeviceState.DISCONNECTED, DeviceState.ADB],
        DeviceState.RECOVERY: [DeviceState.DISCONNECTED, DeviceState.ADB, DeviceState.SIDELOAD],
        DeviceState.SIDELOAD: [DeviceState.DISCONNECTED, DeviceState.RECOVERY],
        DeviceState.FASTBOOT: [DeviceState.DISCONNECTED, DeviceState.FASTBOOTD, DeviceState.EDL,
                               DeviceState.FLASHING, DeviceState.REBOOTING, DeviceState.BUSY],
        DeviceState.FASTBOOTD: [DeviceState.DISCONNECTED, DeviceState.FASTBOOT, DeviceState.FLASHING],
        DeviceState.EDL: [DeviceState.DISCONNECTED, DeviceState.FASTBOOT],
        DeviceState.BROM: [DeviceState.DISCONNECTED],
        DeviceState.FLASHING: [DeviceState.DISCONNECTED, DeviceState.ADB, DeviceState.FASTBOOT, DeviceState.FAILED],
        DeviceState.REBOOTING: [DeviceState.DISCONNECTED, DeviceState.ADB, DeviceState.FASTBOOT],
        DeviceState.BUSY: [DeviceState.DISCONNECTED, DeviceState.ADB, DeviceState.FASTBOOT, DeviceState.FAILED],
        DeviceState.FAILED: [DeviceState.DISCONNECTED, DeviceState.DETECTING],
    }


@dataclass
class DeviceContext:
    """Context for each device."""
    serial: str
    state: DeviceState = DeviceState.DISCONNECTED
    last_state_change: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    error_message: str = ""


class DeviceStateMachine:
    """Manages state transitions for multiple devices."""
    
    def __init__(self, on_state_change: Optional[Callable] = None):
        self._devices: Dict[str, DeviceContext] = {}
        self._lock = threading.Lock()
        self._on_state_change = on_state_change
        self._transition_times: Dict[str, List[Dict]] = {}
    
    def get_or_create(self, serial: str) -> DeviceContext:
        """Get existing or create new device context."""
        with self._lock:
            if serial not in self._devices:
                self._devices[serial] = DeviceContext(serial=serial)
                self._transition_times[serial] = []
            return self._devices[serial]
    
    def get_state(self, serial: str) -> DeviceState:
        """Get current state of a device."""
        with self._lock:
            if serial in self._devices:
                return self._devices[serial].state
            return DeviceState.DISCONNECTED
    
    def transition(self, serial: str, new_state: DeviceState, 
                   metadata: Optional[Dict] = None) -> bool:
        """Transition device to new state if allowed."""
        with self._lock:
            if serial not in self._devices:
                self._devices[serial] = DeviceContext(serial=serial)
            
            ctx = self._devices[serial]
            old_state = ctx.state
            
            # Check if transition is allowed
            if new_state not in StateTransition.ALLOWED.get(old_state, []):
                print(f"[StateMachine] Invalid transition: {old_state.value} -> {new_state.value} for {serial}")
                return False
            
            # Perform transition
            ctx.state = new_state
            ctx.last_state_change = time.time()
            if metadata:
                ctx.metadata.update(metadata)
            
            # Record transition
            if serial not in self._transition_times:
                self._transition_times[serial] = []
            self._transition_times[serial].append({
                'from': old_state.value,
                'to': new_state.value,
                'timestamp': ctx.last_state_change
            })
            
            # Keep only last 100 transitions
            if len(self._transition_times[serial]) > 100:
                self._transition_times[serial] = self._transition_times[serial][-100:]
            
            print(f"[StateMachine] {serial}: {old_state.value} -> {new_state.value}")
            
            # Notify callback
            if self._on_state_change:
                self._on_state_change(serial, old_state, new_state, metadata)
            
            return True
    
    def transition_to_string(self, serial: str, state_str: str, 
                             metadata: Optional[Dict] = None) -> bool:
        """Transition using string state name."""
        try:
            new_state = DeviceState(state_str)
            return self.transition(serial, new_state, metadata)
        except ValueError:
            return False
    
    def is_busy(self, serial: str) -> bool:
        """Check if device is currently busy."""
        state = self.get_state(serial)
        return state in [DeviceState.FLASHING, DeviceState.REBOOTING, DeviceState.BUSY]
    
    def can_operate(self, serial: str) -> bool:
        """Check if device can accept new operations."""
        state = self.get_state(serial)
        return state in [DeviceState.ADB, DeviceState.FASTBOOT, DeviceState.FASTBOOTD, DeviceState.EDL]
    
    def get_all_devices(self) -> Dict[str, DeviceContext]:
        """Get all devices with their contexts."""
        with self._lock:
            return self._devices.copy()
    
    def reset(self, serial: str):
        """Reset device to disconnected state."""
        self.transition(serial, DeviceState.DISCONNECTED)
    
    def clear(self):
        """Clear all devices."""
        with self._lock:
            self._devices.clear()
            self._transition_times.clear()
    
    def get_transition_history(self, serial: str, limit: int = 20) -> List[Dict]:
        """Get transition history for a device."""
        with self._lock:
            if serial in self._transition_times:
                return self._transition_times[serial][-limit:]
            return []


# Global instance for easy import
device_state_machine = DeviceStateMachine()