"""
Pixel Orchestrator Core Package – Minimal exports.
"""
# New V2 modules
from .hwid import get_hwid, verify_hwid, register_hwid
from .base_module import BaseModule
from .module_loader import discover_modules
from .async_transport_v2 import async_transport_v2, AsyncTransportV2, CommandResult
from .operation_manager import OperationManager, Job, JobStatus, JobPriority

# Existing components (if needed for compatibility)
try:
    from .safe_logger import safe_logger
    from .adb_manager import AdbManager
    from .fastboot_manager import FastbootManager
    from .device_state import DeviceDetector
    from .partition_manager import PartitionManager
    from .flashing_engine import FlashingEngine
    from .backup_engine import BackupEngine
    from .restore_engine import RestoreEngine
    from .state_orchestrator import StateOrchestrator
except ImportError:
    pass

__all__ = [
    "get_hwid", "verify_hwid", "register_hwid",
    "BaseModule", "discover_modules",
    "async_transport_v2", "AsyncTransportV2", "CommandResult",
    "OperationManager", "Job", "JobStatus", "JobPriority",
    "safe_logger", "AdbManager", "FastbootManager", "DeviceDetector",
    "PartitionManager", "FlashingEngine", "BackupEngine", "RestoreEngine", "StateOrchestrator"
]
