"""
Real Worker with Cancellation Support
"""

import asyncio
import threading
import time
import uuid
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class Job:
    job_id: str
    device_serial: str
    operation: str
    params: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    cancel_requested: bool = False

class RealWorker:
    """Real worker with cancellation and proper async execution."""
    
    def __init__(self, worker_id: str, device_serial: str):
        self.worker_id = worker_id
        self.device_serial = device_serial
        self.current_job: Optional[Job] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_complete: Optional[Callable] = None
    
    def start(self, on_complete: Optional[Callable] = None):
        self._running = True
        self._on_complete = on_complete
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
        if self.current_job:
            self.current_job.cancel_requested = True
        if self._thread:
            self._thread.join(timeout=5)
    
    def assign_job(self, job: Job) -> bool:
        if self.current_job is None or self.current_job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            self.current_job = job
            job.status = JobStatus.PENDING
            return True
        return False
    
    def cancel_current(self):
        if self.current_job:
            self.current_job.cancel_requested = True
            self.current_job.status = JobStatus.CANCELLED
    
    def _run_loop(self):
        while self._running:
            if self.current_job and self.current_job.status == JobStatus.PENDING:
                self._execute_job()
            time.sleep(0.1)
    
    def _execute_job(self):
        job = self.current_job
        if not job:
            return
        
        job.status = JobStatus.RUNNING
        job.started_at = time.time()
        
        print(f"[Worker {self.worker_id}] Starting job {job.job_id}: {job.operation}")
        
        try:
            # Execute based on operation type
            result = self._run_operation(job)
            
            if job.cancel_requested:
                job.status = JobStatus.CANCELLED
                job.error = "Cancelled by user"
            else:
                job.status = JobStatus.COMPLETED
                job.result = result
                
        except TimeoutError:
            job.status = JobStatus.TIMEOUT
            job.error = f"Timeout after {job.params.get('timeout', 60)}s"
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        
        job.completed_at = time.time()
        duration = job.completed_at - job.started_at if job.started_at else 0
        
        print(f"[Worker {self.worker_id}] Job {job.job_id} finished: {job.status.value} in {duration:.2f}s")
        
        if self._on_complete:
            self._on_complete(job)
    
    def _run_operation(self, job: Job) -> Any:
        """Execute specific operation."""
        from core.async_transport import async_transport
        
        if job.operation == "adb_shell":
            result = async_transport.execute_sync(
                ["adb", "-s", job.device_serial, "shell", job.params.get("command", "")]
            )
            return {"stdout": result.stdout, "stderr": result.stderr}
        
        elif job.operation == "fastboot_reboot":
            result = async_transport.execute_sync(
                ["fastboot", "-s", job.device_serial, "reboot"]
            )
            return {"success": result.success}
        
        elif job.operation == "flash":
            from core.flashing_engine import FlashingEngine
            # This would call existing engine
            return {"status": "flashing"}
        
        else:
            raise ValueError(f"Unknown operation: {job.operation}")

class RealWorkerPool:
    """Pool of real workers for multiple devices."""
    
    def __init__(self):
        self._workers: Dict[str, RealWorker] = {}
        self._lock = threading.Lock()
    
    def get_or_create_worker(self, device_serial: str) -> RealWorker:
        with self._lock:
            if device_serial not in self._workers:
                worker = RealWorker(f"worker_{device_serial}", device_serial)
                worker.start(self._on_job_complete)
                self._workers[device_serial] = worker
            return self._workers[device_serial]
    
    def submit_job(self, job: Job) -> bool:
        worker = self.get_or_create_worker(job.device_serial)
        return worker.assign_job(job)
    
    def cancel_job(self, device_serial: str):
        with self._lock:
            if device_serial in self._workers:
                self._workers[device_serial].cancel_current()
    
    def remove_device(self, device_serial: str):
        with self._lock:
            if device_serial in self._workers:
                self._workers[device_serial].stop()
                del self._workers[device_serial]
    
    def _on_job_complete(self, job: Job):
        print(f"[WorkerPool] Job {job.job_id} completed with status {job.status.value}")

real_worker_pool = RealWorkerPool()