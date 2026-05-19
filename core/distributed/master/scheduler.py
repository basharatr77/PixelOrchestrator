import threading
import time
import logging
from collections import deque
from typing import Dict, List, Optional, Any
from core.distributed.common.message import Message

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.job_queue = deque()  # list of job dicts
        self.workers: Dict[str, dict] = {}  # worker_id -> {status, active_jobs, last_heartbeat}
        self.device_map: Dict[str, str] = {}  # device_id -> worker_id
        self._lock = threading.Lock()
        self._job_counter = 0

    def register_worker(self, worker_id: str):
        with self._lock:
            self.workers[worker_id] = {"status": "idle", "active_jobs": 0, "last_heartbeat": time.time()}
            logger.info(f"Worker {worker_id} registered")

    def heartbeat(self, worker_id: str):
        with self._lock:
            if worker_id in self.workers:
                self.workers[worker_id]["last_heartbeat"] = time.time()
                self.workers[worker_id]["status"] = "alive"

    def submit_job(self, job: dict) -> str:
        """Submit a job (DAG node) to the queue."""
        with self._lock:
            self._job_counter += 1
            job_id = f"job_{self._job_counter}"
            job["job_id"] = job_id
            job["status"] = "queued"
            job["created_at"] = time.time()
            self.job_queue.append(job)
            logger.info(f"Job {job_id} queued")
            return job_id

    def dispatch_next(self) -> Optional[tuple]:
        """Assign next pending job to an available worker. Returns (worker_id, job) or None."""
        with self._lock:
            if not self.job_queue:
                return None
            # Find first idle worker with least active jobs
            available = [(wid, info["active_jobs"]) for wid, info in self.workers.items()
                         if info.get("status") in ("idle", "alive")]
            if not available:
                return None
            # Simple round-robin: pick worker with least active jobs
            available.sort(key=lambda x: x[1])
            worker_id = available[0][0]
            job = self.job_queue.popleft()
            job["status"] = "assigned"
            job["assigned_to"] = worker_id
            job["assigned_at"] = time.time()
            self.workers[worker_id]["active_jobs"] += 1
            logger.info(f"Dispatched job {job['job_id']} to worker {worker_id}")
            return (worker_id, job)

    def mark_job_complete(self, job_id: str, worker_id: str, success: bool):
        with self._lock:
            if worker_id in self.workers:
                self.workers[worker_id]["active_jobs"] = max(0, self.workers[worker_id]["active_jobs"] - 1)
            logger.info(f"Job {job_id} completed with success={success}")

    def mark_worker_dead(self, worker_id: str):
        with self._lock:
            if worker_id in self.workers:
                self.workers[worker_id]["status"] = "dead"
                # Reassign all jobs assigned to this worker
                reassigned = []
                for job in list(self.job_queue):
                    if job.get("assigned_to") == worker_id:
                        job["status"] = "queued"
                        job["assigned_to"] = None
                        reassigned.append(job["job_id"])
                for job in reassigned:
                    logger.info(f"Reassigned job {job} from dead worker {worker_id}")
                # Also clean device locks held by this worker
                devices_to_remove = [dev for dev, wid in self.device_map.items() if wid == worker_id]
                for dev in devices_to_remove:
                    del self.device_map[dev]
                    logger.info(f"Released device {dev} from dead worker {worker_id}")

    def get_alive_workers(self) -> set:
        with self._lock:
            return {wid for wid, info in self.workers.items() if info.get("status") != "dead"}

    def release_device(self, device_id: str):
        with self._lock:
            if device_id in self.device_map:
                del self.device_map[device_id]
