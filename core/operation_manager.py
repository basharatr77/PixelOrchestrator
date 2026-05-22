import uuid
import time
import threading
import json
import sqlite3
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from queue import PriorityQueue

from core.safe_logger import safe_logger
from core.async_transport_v2 import async_transport_v2
from core.device_state_machine import DeviceState, DeviceStateMachine
from core.logger import log_event
from core.event_bus import event_bus, Event, EventType
from core.supervisor import TaskSupervisor
from PySide6.QtCore import QMetaObject, Q_ARG, Qt

# ========== Job Status & Priority ==========
class JobStatus(Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class JobPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Job:
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
    error: Optional[str] = None
    result: Optional[Any] = None
    cancel_requested: bool = False

# ========== Operation Manager ==========
class OperationManager:
    def __init__(self, launcher=None, db_path: str = "jobs.db"):
        self.launcher = launcher
        self.db_path = db_path
        self._jobs: Dict[str, Job] = {}
        self._queue = PriorityQueue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._handlers: Dict[str, Callable] = {}
        self._device_state_machines: Dict[str, DeviceStateMachine] = {}
        self._supervisor = TaskSupervisor()
        self._init_db()
        self._load_pending_jobs()
        self._register_default_handlers()
        # Start event bus (async) – will be run in a separate event loop
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_event_loop, daemon=True).start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(event_bus.start())
        self._loop.run_forever()

    def _init_db(self):
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
                error TEXT,
                result TEXT,
                cancel_requested INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
        conn.commit()
        conn.close()

    def _save_job(self, job: Job):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        data = {
            "id": job.id, "device_serial": job.device_serial, "operation": job.operation,
            "params": json.dumps(job.params), "priority": job.priority.value,
            "status": job.status.value, "retries": job.retries, "max_retries": job.max_retries,
            "timeout": job.timeout, "created_at": job.created_at,
            "started_at": job.started_at, "completed_at": job.completed_at,
            "error": job.error, "result": json.dumps(job.result) if job.result else None,
            "cancel_requested": 1 if job.cancel_requested else 0
        }
        conn.execute("""
            INSERT OR REPLACE INTO jobs (id, device_serial, operation, params, priority, status,
                retries, max_retries, timeout, created_at, started_at, completed_at,
                error, result, cancel_requested)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data["id"], data["device_serial"], data["operation"], data["params"],
              data["priority"], data["status"], data["retries"], data["max_retries"],
              data["timeout"], data["created_at"], data["started_at"], data["completed_at"],
              data["error"], data["result"], data["cancel_requested"]))
        conn.commit()
        conn.close()

    def _load_pending_jobs(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.execute("SELECT * FROM jobs WHERE status IN ('created', 'queued', 'running')")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        for row in rows:
            data = dict(zip(columns, row))
            job = Job(
                id=data["id"],
                device_serial=data["device_serial"],
                operation=data["operation"],
                params=json.loads(data["params"]),
                priority=JobPriority(data["priority"]),
                max_retries=data["max_retries"],
                timeout=data["timeout"]
            )
            job.status = JobStatus(data["status"])
            job.retries = data["retries"]
            job.started_at = data["started_at"]
            job.completed_at = data["completed_at"]
            job.error = data["error"]
            job.cancel_requested = bool(data["cancel_requested"])
            if data["result"]:
                job.result = json.loads(data["result"])
            self._jobs[job.id] = job
            if job.status in (JobStatus.CREATED, JobStatus.QUEUED):
                self._queue.put((job.priority.value, job.created_at, job.id))

    def _register_default_handlers(self):
        # Handlers will be registered externally
        pass

    def register_handler(self, operation: str, handler: Callable):
        self._handlers[operation] = handler

    def create_job(self, device_serial: str, operation: str, params: Dict,
                   priority: JobPriority = JobPriority.NORMAL,
                   max_retries: int = 3, timeout: int = 60) -> str:
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
        self._queue.put((priority.value, job.created_at, job_id))
        log_event(device_serial, operation, "INFO", f"Job created: {job_id[:8]}")
        event_bus.emit(Event(EventType.JOB_CREATED, {"job_id": job_id, "operation": operation}, "op_manager"))
        return job_id

    def start(self):
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        log_event("system", "manager", "INFO", "Operation Manager started")

    def _worker_loop(self):
        while self._running:
            try:
                priority, timestamp, job_id = self._queue.get(timeout=1)
                if job_id not in self._jobs:
                    continue
                job = self._jobs[job_id]
                if job.status in [JobStatus.COMPLETED, JobStatus.CANCELLED]:
                    continue
                if job.status == JobStatus.RUNNING:
                    continue
                self._execute_job(job_id)
            except Exception as e:
                if "Empty" not in str(e):
                    log_event("system", "worker", "ERROR", str(e))

    def _execute_job(self, job_id: str):
        job = self._jobs.get(job_id)
        if not job:
            return
        handler = self._handlers.get(job.operation)
        if not handler:
            self._mark_failed(job_id, f"No handler for: {job.operation}")
            return
        try:
            # Ensure device state machine exists
            if job.device_serial not in self._device_state_machines:
                self._device_state_machines[job.device_serial] = DeviceStateMachine(job.device_serial)
            # Check if device is in a valid state for this operation (custom logic per job)
            # For now, just proceed; we'll enhance later.
            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            self._save_job(job)
            log_event(job.device_serial, job.operation, "INFO", f"Executing job {job_id[:8]}")
            event_bus.emit(Event(EventType.JOB_CREATED, {"job_id": job_id, "status": "running"}, "op_manager"))
            result = handler(job)
            if result:
                self._mark_completed(job_id, result)
            else:
                self._mark_failed(job_id, "Handler returned False")
        except Exception as e:
            self._mark_failed(job_id, str(e))

    def _mark_completed(self, job_id: str, result: Any):
        job = self._jobs.get(job_id)
        if not job:
            return
        job.status = JobStatus.COMPLETED
        job.completed_at = time.time()
        job.result = result
        self._save_job(job)
        log_event(job.device_serial, job.operation, "INFO", f"Job completed: {job_id[:8]}")
        event_bus.emit(Event(EventType.JOB_COMPLETED, {"job_id": job_id, "result": str(result)[:100]}, "op_manager"))

    def _mark_failed(self, job_id: str, error: str):
        job = self._jobs.get(job_id)
        if not job:
            return
        job.status = JobStatus.FAILED
        job.completed_at = time.time()
        job.error = error
        self._save_job(job)
        log_event(job.device_serial, job.operation, "ERROR", error)
        event_bus.emit(Event(EventType.ERROR, {"job_id": job_id, "error": error}, "op_manager"))

    async def update_job_status(self, job_id: str, status: str, result: str = None, error: str = None):
        if job_id in self._jobs:
            job = self._jobs[job_id]
            job.status = JobStatus(status)
            if result:
                job.result = result
            if error:
                job.error = error
            if status in ["COMPLETED", "FAILED", "CANCELLED"]:
                job.completed_at = time.time()
            self._save_job(job)

    async def _handle_mediatek_job_async(self, job: Job):
        # ... (same as before, but now with structured logging)
        params = job.params
        op = params.get("sub_operation")
        scatter = params.get("scatter_path", "")
        auto_reboot = params.get("auto_reboot", False)

        if op == "flash" and scatter:
            cmd = ["mtk", "f", "--scatter", scatter]
            if auto_reboot:
                cmd.append("--reboot")
        elif op == "format":
            cmd = ["mtk", "e", "all"]
        elif op == "frp":
            cmd = ["mtk", "frp"]
        elif op == "unlock":
            cmd = ["mtk", "unlock"]
        elif op == "auth":
            cmd = ["mtk", "exploit"]
        elif op == "erase":
            cmd = ["mtk", "e", scatter]
        else:
            await self.update_job_status(job.id, "FAILED", error=f"Unknown MTK op: {op}")
            return False

        await self.update_job_status(job.id, "RUNNING")
        log_event(job.device_serial, f"mtk_{op}", "INFO", f"Starting MediaTek operation: {op}")

        def stream_to_ui(line_text):
            if self.launcher and hasattr(self.launcher, "active_modules") and "MediaTek" in self.launcher.active_modules:
                ui_module = self.launcher.active_modules["MediaTek"]
                QMetaObject.invokeMethod(ui_module, "log_message", Qt.QueuedConnection, Q_ARG(str, line_text))

        try:
            result = await async_transport_v2.execute_command_async(cmd, job_id=job.id, log_callback=stream_to_ui)
            if result.success:
                await self.update_job_status(job.id, "COMPLETED", result=result.stdout)
                log_event(job.device_serial, f"mtk_{op}", "INFO", "Operation completed")
                return True
            else:
                await self.update_job_status(job.id, "FAILED", error=result.stderr)
                log_event(job.device_serial, f"mtk_{op}", "ERROR", result.stderr)
                return False
        except Exception as e:
            await self.update_job_status(job.id, "FAILED", error=str(e))
            log_event(job.device_serial, f"mtk_{op}", "ERROR", str(e))
            return False

    def _handle_mediatek_job_sync(self, job: Job):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._handle_mediatek_job_async(job), loop)
            return future.result()
        else:
            return asyncio.run(self._handle_mediatek_job_async(job))

    async def _handle_qualcomm_job_async(self, job: Job):
        # Similar to your existing qualcomm handler (keep the same logic)
        # ... (I'll skip for brevity, but include when you need it)
        pass

    def _handle_qualcomm_job_sync(self, job: Job):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._handle_qualcomm_job_async(job), loop)
            return future.result()
        else:
            return asyncio.run(self._handle_qualcomm_job_async(job))

    def stop(self):
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        asyncio.run_coroutine_threadsafe(event_bus.stop(), self._loop)