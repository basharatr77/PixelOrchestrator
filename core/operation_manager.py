"""
Operation Manager – Job Lifecycle Management
Manages creation, queuing, execution, retry, cancellation, and recovery of operations
"""

import uuid
import time
import threading
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from queue import Queue, PriorityQueue

from core.async_transport_v2 import async_transport_v2
from core.safe_logger import safe_logger
from core.event_bus_v2 import EventBus, Event, EventType, event_bus


class OperationStatus(Enum):
    """All possible states of an operation in its lifecycle."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class OperationPriority(Enum):
    """Priority levels for operations."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Operation:
    """Represents a single operation/job in the system."""
    id: str
    device_serial: str
    type: str
    params: Dict[str, Any]
    priority: OperationPriority = OperationPriority.NORMAL
    status: OperationStatus = OperationStatus.CREATED
    retries: int = 0
    max_retries: int = 3
    timeout: int = 60
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    last_retry_at: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    cancel_requested: bool = False
    
    def to_dict(self) -> Dict:
        """Convert operation to dictionary for serialization."""
        return {
            "id": self.id,
            "device_serial": self.device_serial,
            "type": self.type,
            "params": self.params,
            "priority": self.priority.value,
            "status": self.status.value,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "last_retry_at": self.last_retry_at,
            "error": self.error,
            "result": self.result
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Operation":
        """Create operation from dictionary."""
        op = cls(
            id=data["id"],
            device_serial=data["device_serial"],
            type=data["type"],
            params=data["params"],
            priority=OperationPriority(data.get("priority", 1)),
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 60)
        )
        op.status = OperationStatus(data.get("status", "created"))
        op.retries = data.get("retries", 0)
        op.started_at = data.get("started_at")
        op.completed_at = data.get("completed_at")
        op.last_retry_at = data.get("last_retry_at")
        op.error = data.get("error")
        op.result = data.get("result")
        return op
    
    @property
    def duration(self) -> float:
        """Calculate operation duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return time.time() - self.started_at
        return 0
    
    @property
    def can_retry(self) -> bool:
        """Check if operation can be retried."""
        return (self.status in [OperationStatus.FAILED, OperationStatus.TIMEOUT] and
                self.retries < self.max_retries and
                not self.cancel_requested)


class OperationManager:
    """
    Central operation manager for job lifecycle management.
    Handles creation, queuing, execution, retry, cancellation, and recovery.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._operations: Dict[str, Operation] = {}
        self._device_operations: Dict[str, List[str]] = {}  # device_serial -> [op_ids]
        self._queue = PriorityQueue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._recovery_thread: Optional[threading.Thread] = None
        self._operation_handlers: Dict[str, Callable] = {}
        
        self._register_default_handlers()
        
        safe_logger.log_signal.connect(lambda msg: None)  # Connection for logging
        self.log("Operation Manager initialized")
    
    def _register_default_handlers(self):
        """Register default operation handlers."""
        self.register_handler("adb_reboot", self._handle_adb_reboot)
        self.register_handler("adb_shell", self._handle_adb_shell)
        self.register_handler("fastboot_reboot", self._handle_fastboot_reboot)
        self.register_handler("fastboot_flash", self._handle_fastboot_flash)
        self.register_handler("screenshot", self._handle_screenshot)
    
    def log(self, msg: str):
        """Thread-safe logging."""
        safe_logger.log(f"[OpManager] {msg}")
    
    # ========== HANDLER REGISTRATION ==========
    def register_handler(self, operation_type: str, handler: Callable):
        """Register a handler for a specific operation type."""
        self._operation_handlers[operation_type] = handler
        self.log(f"Registered handler for: {operation_type}")
    
    # ========== OPERATION LIFECYCLE ==========
    def create_operation(self, device_serial: str, op_type: str, 
                         params: Dict[str, Any],
                         priority: OperationPriority = OperationPriority.NORMAL,
                         max_retries: int = 3,
                         timeout: int = 60) -> str:
        """Create a new operation and add to queue."""
        op_id = str(uuid.uuid4())
        
        operation = Operation(
            id=op_id,
            device_serial=device_serial,
            type=op_type,
            params=params,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        with self._lock:
            self._operations[op_id] = operation
            
            if device_serial not in self._device_operations:
                self._device_operations[device_serial] = []
            self._device_operations[device_serial].append(op_id)
        
        # Add to priority queue (negative priority for higher first)
        self._queue.put((-priority.value, op_id))
        
        self.log(f"Operation created: {op_id} ({op_type} on {device_serial})")
        
        # Emit event
        event_bus.emit(Event(
            type=EventType.JOB_START,
            data={"job_id": op_id, "type": op_type, "serial": device_serial}
        ))
        
        return op_id
    
    def start_operation(self, op_id: str) -> bool:
        """Start a specific operation (force start)."""
        with self._lock:
            if op_id not in self._operations:
                return False
            
            op = self._operations[op_id]
            if op.status != OperationStatus.CREATED:
                return False
            
            op.status = OperationStatus.QUEUED
        
        self.log(f"Operation queued: {op_id}")
        return True
    
    def cancel_operation(self, op_id: str) -> bool:
        """Cancel an operation."""
        with self._lock:
            if op_id not in self._operations:
                return False
            
            op = self._operations[op_id]
            if op.status in [OperationStatus.COMPLETED, OperationStatus.CANCELLED]:
                return False
            
            if op.status == OperationStatus.RUNNING:
                op.cancel_requested = True
                # Also cancel via transport
                async_transport_v2.cancel_command(op_id)
            
            op.status = OperationStatus.CANCELLED
            op.completed_at = time.time()
            
            self.log(f"Operation cancelled: {op_id}")
            return True
    
    def retry_operation(self, op_id: str) -> bool:
        """Manually retry a failed operation."""
        with self._lock:
            if op_id not in self._operations:
                return False
            
            op = self._operations[op_id]
            if not op.can_retry:
                return False
            
            op.status = OperationStatus.RETRYING
            op.retries += 1
            op.last_retry_at = time.time()
            op.error = None
        
        self._queue.put((-op.priority.value, op_id))
        self.log(f"Operation retry requested: {op_id} (attempt {op.retries})")
        return True
    
    def get_operation(self, op_id: str) -> Optional[Operation]:
        """Get operation by ID."""
        with self._lock:
            return self._operations.get(op_id)
    
    def get_status(self, op_id: str) -> Optional[OperationStatus]:
        """Get operation status."""
        op = self.get_operation(op_id)
        return op.status if op else None
    
    def list_operations(self, device_serial: Optional[str] = None) -> List[Operation]:
        """List all operations, optionally filtered by device."""
        with self._lock:
            if device_serial:
                op_ids = self._device_operations.get(device_serial, [])
                return [self._operations[oid] for oid in op_ids if oid in self._operations]
            return list(self._operations.values())
    
    def get_device_queue(self, device_serial: str) -> List[Operation]:
        """Get pending operations for a device."""
        with self._lock:
            op_ids = self._device_operations.get(device_serial, [])
            return [self._operations[oid] for oid in op_ids 
                    if oid in self._operations and 
                    self._operations[oid].status in [OperationStatus.CREATED, OperationStatus.QUEUED, OperationStatus.RETRYING]]
    
    # ========== EXECUTION ==========
    def start(self):
        """Start the operation manager (worker and recovery threads)."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self._recovery_thread = threading.Thread(target=self._recovery_loop, daemon=True)
        self._recovery_thread.start()
        
        self.log("Operation Manager started")
    
    def stop(self):
        """Stop the operation manager."""
        self._running = False
        self.log("Operation Manager stopped")
    
    def _worker_loop(self):
        """Main worker loop that processes operations from queue."""
        while self._running:
            try:
                # Get next operation from queue
                priority, op_id = self._queue.get(timeout=1)
                
                with self._lock:
                    if op_id not in self._operations:
                        continue
                    
                    op = self._operations[op_id]
                    
                    # Skip if already completed or cancelled
                    if op.status in [OperationStatus.COMPLETED, OperationStatus.CANCELLED]:
                        continue
                    
                    # Check if operation is already running or completed
                    if op.status == OperationStatus.RUNNING:
                        continue
                    
                    op.status = OperationStatus.RUNNING
                    op.started_at = time.time()
                    op.cancel_requested = False
                
                # Execute the operation
                self._execute_operation(op_id)
                
            except Exception as e:
                if "Empty" not in str(e):
                    self.log(f"Worker loop error: {e}")
    
    def _execute_operation(self, op_id: str):
        """Execute a single operation."""
        with self._lock:
            if op_id not in self._operations:
                return
            op = self._operations[op_id]
        
        self.log(f"Executing operation: {op_id} ({op.type} on {op.device_serial})")
        
        handler = self._operation_handlers.get(op.type)
        if not handler:
            self._mark_failed(op_id, f"No handler registered for operation type: {op.type}")
            return
        
        try:
            # Execute with timeout
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(handler, op)
                try:
                    result = future.result(timeout=op.timeout)
                    self._mark_completed(op_id, result)
                except concurrent.futures.TimeoutError:
                    self._mark_failed(op_id, f"Timeout after {op.timeout}s")
                    async_transport_v2.cancel_command(op_id)
                    
        except Exception as e:
            self._mark_failed(op_id, str(e))
    
    def _mark_completed(self, op_id: str, result: Any):
        """Mark operation as completed."""
        with self._lock:
            if op_id not in self._operations:
                return
            op = self._operations[op_id]
            op.status = OperationStatus.COMPLETED
            op.completed_at = time.time()
            op.result = result
        
        self.log(f"Operation completed: {op_id} (duration: {op.duration:.2f}s)")
        event_bus.emit(Event(
            type=EventType.JOB_END,
            data={"job_id": op_id, "success": True, "duration": op.duration}
        ))
    
    def _mark_failed(self, op_id: str, error: str):
        """Mark operation as failed, with auto-retry if possible."""
        with self._lock:
            if op_id not in self._operations:
                return
            op = self._operations[op_id]
            op.error = error
            op.completed_at = time.time()
            
            if op.can_retry:
                op.status = OperationStatus.RETRYING
                op.retries += 1
                op.last_retry_at = time.time()
                self._queue.put((-op.priority.value, op_id))
                self.log(f"Operation will retry: {op_id} (attempt {op.retries}/{op.max_retries})")
            else:
                op.status = OperationStatus.FAILED
                self.log(f"Operation failed: {op_id} - {error}")
                event_bus.emit(Event(
                    type=EventType.JOB_FAILED,
                    data={"job_id": op_id, "error": error}
                ))
    
    def _recovery_loop(self):
        """Recovery loop to handle orphaned or stuck operations."""
        while self._running:
            time.sleep(30)  # Check every 30 seconds
            
            try:
                with self._lock:
                    for op_id, op in list(self._operations.items()):
                        # Check for stuck running operations
                        if op.status == OperationStatus.RUNNING and op.started_at:
                            duration = time.time() - op.started_at
                            if duration > op.timeout + 10:
                                self.log(f"Recovery: Operation {op_id} appears stuck, marking as timeout")
                                self._mark_failed(op_id, "Recovery: Operation timed out")
                        
                        # Check for waiting operations that never started
                        elif op.status == OperationStatus.WAITING and op.created_at:
                            wait_time = time.time() - op.created_at
                            if wait_time > 300:  # 5 minutes
                                self.log(f"Recovery: Operation {op_id} abandoned, cleaning up")
                                op.status = OperationStatus.FAILED
                                op.error = "Recovery: Operation abandoned"
                
                # Also recover any pending transport commands
                async_transport_v2.recover_pending_commands()
                
            except Exception as e:
                self.log(f"Recovery loop error: {e}")
    
    # ========== DEFAULT HANDLERS ==========
    def _handle_adb_reboot(self, op: Operation) -> Dict:
        """Handle adb reboot operation."""
        import asyncio
        target = op.params.get("target", "")
        result = asyncio.run(async_transport_v2.adb_reboot(op.device_serial, target))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr}
    
    def _handle_adb_shell(self, op: Operation) -> Dict:
        """Handle adb shell operation."""
        import asyncio
        command = op.params.get("command", "")
        result = asyncio.run(async_transport_v2.adb_shell(op.device_serial, command))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr}
    
    def _handle_fastboot_reboot(self, op: Operation) -> Dict:
        """Handle fastboot reboot operation."""
        import asyncio
        target = op.params.get("target", "")
        result = asyncio.run(async_transport_v2.fastboot_reboot(op.device_serial, target))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr}
    
    def _handle_fastboot_flash(self, op: Operation) -> Dict:
        """Handle fastboot flash operation."""
        import asyncio
        partition = op.params.get("partition", "")
        image = op.params.get("image", "")
        result = asyncio.run(async_transport_v2.fastboot_flash(op.device_serial, partition, image))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr}
    
    def _handle_screenshot(self, op: Operation) -> Dict:
        """Handle screenshot operation."""
        import asyncio
        result = asyncio.run(async_transport_v2.take_screenshot(op.device_serial))
        return {"success": result.success, "filename": result.stdout.strip() if result.success else None}


# Global instance
operation_manager = OperationManager()