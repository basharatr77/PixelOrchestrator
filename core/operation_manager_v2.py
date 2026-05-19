"""
Operation Manager V2 – Production Grade Job Lifecycle Management
Supports: Creation, Queue, Retry, Cancel, Recovery, Persistence
"""

import uuid
import time
import threading
import json
import sqlite3
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from queue import PriorityQueue
from datetime import datetime

from core.safe_logger import safe_logger
from core.event_bus_v2 import EventBus, Event, EventType, event_bus


class JobStatus(Enum):
    """Complete job lifecycle states."""
    CREATED = "created"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    WAITING = "waiting"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Job:
    """Complete job definition with all metadata."""
    id: str
    device_serial: str
    operation: str
    params: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.CREATED
    retries: int = 0
    max_retries: int = 3
    timeout: int = 60
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    last_retry_at: Optional[float] = None
    assigned_worker: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    cancel_requested: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "device_serial": self.device_serial,
            "operation": self.operation,
            "params": json.dumps(self.params),
            "priority": self.priority.value,
            "status": self.status.value,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "last_retry_at": self.last_retry_at,
            "assigned_worker": self.assigned_worker,
            "error": self.error,
            "result": json.dumps(self.result) if self.result else None,
            "cancel_requested": self.cancel_requested
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Job":
        job = cls(
            id=data["id"],
            device_serial=data["device_serial"],
            operation=data["operation"],
            params=json.loads(data["params"]) if isinstance(data["params"], str) else data["params"],
            priority=JobPriority(data.get("priority", 1)),
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 60)
        )
        job.status = JobStatus(data.get("status", "created"))
        job.retries = data.get("retries", 0)
        job.started_at = data.get("started_at")
        job.completed_at = data.get("completed_at")
        job.last_retry_at = data.get("last_retry_at")
        job.assigned_worker = data.get("assigned_worker")
        job.error = data.get("error")
        job.cancel_requested = data.get("cancel_requested", False)
        if data.get("result"):
            job.result = json.loads(data["result"]) if isinstance(data["result"], str) else data["result"]
        return job
    
    @property
    def duration(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return time.time() - self.started_at
        return 0
    
    @property
    def can_retry(self) -> bool:
        return (self.status in [JobStatus.FAILED, JobStatus.TIMEOUT] and
                self.retries < self.max_retries and
                not self.cancel_requested)


class OperationManagerV2:
    """
    Production-grade operation manager with:
    - Job lifecycle management
    - Retry with exponential backoff
    - Persistence (SQLite)
    - Crash recovery
    - Thread-safe
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
    
    def __init__(self, db_path: str = "jobs.db"):
        if self._initialized:
            return
        self._initialized = True
        
        self.db_path = db_path
        self._jobs: Dict[str, Job] = {}
        self._queue = PriorityQueue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._recovery_thread: Optional[threading.Thread] = None
        self._handlers: Dict[str, Callable] = {}
        
        self._init_db()
        self._load_pending_jobs()
        self._register_default_handlers()
        
        safe_logger.log_signal.connect(lambda msg: None)
        self.log("Operation Manager V2 initialized")
    
    def _init_db(self):
        """Initialize SQLite database for job persistence."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                device_serial TEXT NOT NULL,
                operation TEXT NOT NULL,
                params TEXT,
                priority INTEGER,
                status TEXT,
                retries INTEGER,
                max_retries INTEGER,
                timeout INTEGER,
                created_at REAL,
                started_at REAL,
                completed_at REAL,
                last_retry_at REAL,
                assigned_worker TEXT,
                error TEXT,
                result TEXT,
                cancel_requested INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_device ON jobs(device_serial)")
        conn.commit()
        conn.close()
        self.log("Database initialized")
    
    def _load_pending_jobs(self):
        """Load pending jobs from database on startup (crash recovery)."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.execute("""
            SELECT * FROM jobs WHERE status IN ('created', 'queued', 'assigned', 'running', 'retrying')
        """)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        for row in rows:
            data = dict(zip(columns, row))
            job = Job.from_dict(data)
            self._jobs[job.id] = job
            if job.status in [JobStatus.CREATED, JobStatus.QUEUED, JobStatus.RETRYING]:
                self._queue.put((-job.priority.value, job.id))
            self.log(f"Recovered job: {job.id[:8]} (status: {job.status.value})")
        
        self.log(f"Loaded {len(self._jobs)} pending jobs from database")
    
    def _register_default_handlers(self):
        """Register default operation handlers."""
        self.register_handler("adb_reboot", self._handle_adb_reboot)
        self.register_handler("adb_shell", self._handle_adb_shell)
        self.register_handler("fastboot_reboot", self._handle_fastboot_reboot)
        self.register_handler("fastboot_flash", self._handle_fastboot_flash)
    
    def log(self, msg: str):
        safe_logger.log(f"[OpMgrV2] {msg}")
    
    # ========== PUBLIC API ==========
    def register_handler(self, operation: str, handler: Callable):
        """Register a handler for an operation type."""
        self._handlers[operation] = handler
        self.log(f"Registered handler: {operation}")
    
    def create_job(self, device_serial: str, operation: str, params: Dict,
                   priority: JobPriority = JobPriority.NORMAL,
                   max_retries: int = 3, timeout: int = 60) -> str:
        """Create a new job and persist to database."""
        job_id = str(uuid.uuid4())
        
        job = Job(
            id=job_id,
            device_serial=device_serial,
            operation=operation,
            params=params,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        self._jobs[job_id] = job
        self._save_job(job)
        self._queue.put((-priority.value, job_id))
        
        self.log(f"Job created: {job_id[:8]} ({operation} on {device_serial})")
        event_bus.emit(Event(
            type=EventType.JOB_START,
            data={"job_id": job_id, "operation": operation, "serial": device_serial}
        ))
        
        return job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if it's not already completed."""
        if job_id not in self._jobs:
            return False
        
        job = self._jobs[job_id]
        if job.status in [JobStatus.COMPLETED, JobStatus.CANCELLED]:
            return False
        
        job.cancel_requested = True
        job.status = JobStatus.CANCELLED
        job.completed_at = time.time()
        self._save_job(job)
        
        self.log(f"Job cancelled: {job_id[:8]}")
        event_bus.emit(Event(
            type=EventType.JOB_CANCELLED,
            data={"job_id": job_id}
        ))
        return True
    
    def retry_job(self, job_id: str) -> bool:
        """Manually retry a failed job."""
        if job_id not in self._jobs:
            return False
        
        job = self._jobs[job_id]
        if not job.can_retry:
            return False
        
        job.status = JobStatus.RETRYING
        job.retries += 1
        job.last_retry_at = time.time()
        job.error = None
        self._save_job(job)
        self._queue.put((-job.priority.value, job_id))
        
        self.log(f"Job retry requested: {job_id[:8]} (attempt {job.retries})")
        event_bus.emit(Event(
            type=EventType.JOB_RETRY,
            data={"job_id": job_id, "attempt": job.retries}
        ))
        return True
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def get_status(self, job_id: str) -> Optional[JobStatus]:
        job = self.get_job(job_id)
        return job.status if job else None
    
    def list_jobs(self, device_serial: Optional[str] = None) -> List[Job]:
        """List all jobs, optionally filtered by device."""
        if device_serial:
            return [j for j in self._jobs.values() if j.device_serial == device_serial]
        return list(self._jobs.values())
    
    def get_pending_jobs(self, device_serial: Optional[str] = None) -> List[Job]:
        """Get pending jobs (created, queued, retrying)."""
        pending_statuses = [JobStatus.CREATED, JobStatus.QUEUED, JobStatus.RETRYING]
        jobs = self.list_jobs(device_serial)
        return [j for j in jobs if j.status in pending_statuses]
    
    # ========== EXECUTION ==========
    def start(self):
        """Start the operation manager."""
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
        """Main worker loop processing jobs from queue."""
        while self._running:
            try:
                priority, job_id = self._queue.get(timeout=1)
                
                if job_id not in self._jobs:
                    continue
                
                job = self._jobs[job_id]
                
                # Skip if already completed or cancelled
                if job.status in [JobStatus.COMPLETED, JobStatus.CANCELLED]:
                    continue
                
                # Skip if already running
                if job.status == JobStatus.RUNNING:
                    continue
                
                # Execute job
                self._execute_job(job_id)
                
            except Exception as e:
                if "Empty" not in str(e):
                    self.log(f"Worker error: {e}")
    
    def _execute_job(self, job_id: str):
        """Execute a single job."""
        job = self._jobs.get(job_id)
        if not job:
            return
        
        # Update status
        job.status = JobStatus.RUNNING
        job.started_at = time.time()
        self._save_job(job)
        
        self.log(f"Executing job: {job_id[:8]} ({job.operation} on {job.device_serial})")
        event_bus.emit(Event(
            type=EventType.OPERATION_START,
            data={"job_id": job_id, "operation": job.operation}
        ))
        
        handler = self._handlers.get(job.operation)
        if not handler:
            self._mark_failed(job_id, f"No handler for: {job.operation}")
            return
        
        try:
            # Execute with timeout using concurrent.futures
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(handler, job)
                try:
                    result = future.result(timeout=job.timeout)
                    self._mark_completed(job_id, result)
                except concurrent.futures.TimeoutError:
                    self._mark_failed(job_id, f"Timeout after {job.timeout}s")
                    
        except Exception as e:
            self._mark_failed(job_id, str(e))
    
    def _mark_completed(self, job_id: str, result: Any):
        """Mark job as completed."""
        job = self._jobs.get(job_id)
        if not job:
            return
        
        job.status = JobStatus.COMPLETED
        job.completed_at = time.time()
        job.result = result
        self._save_job(job)
        
        self.log(f"Job completed: {job_id[:8]} (duration: {job.duration:.2f}s)")
        event_bus.emit(Event(
            type=EventType.JOB_END,
            data={"job_id": job_id, "success": True, "duration": job.duration}
        ))
    
    def _mark_failed(self, job_id: str, error: str):
        """Mark job as failed, with auto-retry if possible."""
        job = self._jobs.get(job_id)
        if not job:
            return
        
        job.error = error
        job.completed_at = time.time()
        
        if job.can_retry:
            job.status = JobStatus.RETRYING
            job.retries += 1
            job.last_retry_at = time.time()
            self._save_job(job)
            
            # Exponential backoff
            delay = 2 ** job.retries
            self.log(f"Job will retry: {job_id[:8]} (attempt {job.retries}/{job.max_retries}) after {delay}s")
            
            # Schedule retry with delay
            def schedule_retry():
                time.sleep(delay)
                if job_id in self._jobs and self._jobs[job_id].status == JobStatus.RETRYING:
                    self._queue.put((-job.priority.value, job_id))
            
            threading.Thread(target=schedule_retry, daemon=True).start()
        else:
            job.status = JobStatus.FAILED
            self._save_job(job)
            self.log(f"Job failed: {job_id[:8]} - {error}")
            event_bus.emit(Event(
                type=EventType.JOB_FAILED,
                data={"job_id": job_id, "error": error}
            ))
    
    def _recovery_loop(self):
        """Recovery loop for orphaned or stuck jobs."""
        while self._running:
            time.sleep(30)
            
            try:
                for job_id, job in list(self._jobs.items()):
                    # Check stuck running jobs
                    if job.status == JobStatus.RUNNING and job.started_at:
                        duration = time.time() - job.started_at
                        if duration > job.timeout + 30:
                            self.log(f"Recovery: Stuck job {job_id[:8]}, marking as timeout")
                            self._mark_failed(job_id, "Recovery: Job stuck")
                    
                    # Check jobs stuck in retrying
                    elif job.status == JobStatus.RETRYING and job.last_retry_at:
                        wait_time = time.time() - job.last_retry_at
                        if wait_time > 300:
                            self.log(f"Recovery: Job {job_id[:8]} stuck in retry, resetting")
                            self._queue.put((-job.priority.value, job_id))
                
                # Clean old completed jobs (older than 7 days)
                cutoff = time.time() - (7 * 24 * 3600)
                for job_id, job in list(self._jobs.items()):
                    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                        if job.completed_at and job.completed_at < cutoff:
                            self._delete_job(job_id)
                            
            except Exception as e:
                self.log(f"Recovery error: {e}")
    
    def _save_job(self, job: Job):
        """Save job to database."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        data = job.to_dict()
        conn.execute("""
            INSERT OR REPLACE INTO jobs (
                id, device_serial, operation, params, priority, status, retries,
                max_retries, timeout, created_at, started_at, completed_at,
                last_retry_at, assigned_worker, error, result, cancel_requested
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id"], data["device_serial"], data["operation"], data["params"],
            data["priority"], data["status"], data["retries"], data["max_retries"],
            data["timeout"], data["created_at"], data["started_at"], data["completed_at"],
            data["last_retry_at"], data["assigned_worker"], data["error"],
            data["result"], 1 if data["cancel_requested"] else 0
        ))
        conn.commit()
        conn.close()
    
    def _delete_job(self, job_id: str):
        """Delete job from database and memory."""
        if job_id in self._jobs:
            del self._jobs[job_id]
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
        self.log(f"Deleted old job: {job_id[:8]}")
    
    # ========== DEFAULT HANDLERS ==========
    def _handle_adb_reboot(self, job: Job) -> Dict:
        from core.async_transport_v2 import async_transport_v2
        import asyncio
        target = job.params.get("target", "")
        result = asyncio.run(async_transport_v2.adb_reboot(job.device_serial, target))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr}
    
    def _handle_adb_shell(self, job: Job) -> Dict:
        from core.async_transport_v2 import async_transport_v2
        import asyncio
        command = job.params.get("command", "")
        result = asyncio.run(async_transport_v2.adb_shell(job.device_serial, command))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr}
    
    def _handle_fastboot_reboot(self, job: Job) -> Dict:
        from core.async_transport_v2 import async_transport_v2
        import asyncio
        target = job.params.get("target", "")
        result = asyncio.run(async_transport_v2.fastboot_reboot(job.device_serial, target))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr}
    
    def _handle_fastboot_flash(self, job: Job) -> Dict:
        from core.async_transport_v2 import async_transport_v2
        import asyncio
        partition = job.params.get("partition", "")
        image = job.params.get("image", "")
        result = asyncio.run(async_transport_v2.fastboot_flash(job.device_serial, partition, image))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr}


# Global instance
operation_manager_v2 = OperationManagerV2()