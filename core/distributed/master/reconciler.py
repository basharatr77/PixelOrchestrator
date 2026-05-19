import threading
import time
import logging
from core.distributed.master.scheduler import Scheduler

logger = logging.getLogger(__name__)

class JobReconciler:
    def __init__(self, scheduler: Scheduler, interval_sec: int = 10, heartbeat_timeout: int = 30):
        self.scheduler = scheduler
        self.interval = interval_sec
        self.heartbeat_timeout = heartbeat_timeout
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("JobReconciler started")

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        while not self._stop.is_set():
            try:
                self._reconcile()
            except Exception as e:
                logger.error(f"Reconciliation error: {e}")
            time.sleep(self.interval)

    def _reconcile(self):
        # Detect dead workers based on heartbeat timeout
        now = time.time()
        dead_workers = []
        for wid, info in self.scheduler.workers.items():
            if info.get("status") != "dead" and (now - info.get("last_heartbeat", 0)) > self.heartbeat_timeout:
                dead_workers.append(wid)
        for wid in dead_workers:
            logger.warning(f"Worker {wid} considered dead (heartbeat timeout)")
            self.scheduler.mark_worker_dead(wid)
