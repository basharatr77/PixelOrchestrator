import sys
import threading
import time
import logging
from core.transport import Transport
from core.adb_manager import AdbManager
from core.fastboot_manager import FastbootManager
from core.device_state import DeviceDetector
from core.capabilities import CapabilityDetector
from core.partition_manager import PartitionManager
from core.state_orchestrator import StateOrchestrator
from core.flashing_engine import FlashingEngine
from core.backup_engine import BackupEngine
from core.restore_engine import RestoreEngine
from core.distributed.master.scheduler import Scheduler
from core.distributed.master.reconciler import JobReconciler
from core.distributed.transport.websocket_transport import WebSocketTransport
from core.distributed.common.message import Message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Master")

class MasterNode:
    def __init__(self):
        self.scheduler = Scheduler()
        self.reconciler = JobReconciler(self.scheduler)
        self.transport = WebSocketTransport()
        self._init_local_engines()

    def _init_local_engines(self):
        transport = Transport()
        adb = AdbManager(transport)
        fastboot = FastbootManager(transport)
        detector = DeviceDetector(adb, fastboot)
        caps = CapabilityDetector(adb, fastboot)
        part_mgr = PartitionManager(adb, fastboot)
        orchestrator = StateOrchestrator(adb, fastboot, detector, caps, part_mgr)
        self.flasher = FlashingEngine(orchestrator)
        self.backuper = BackupEngine(orchestrator)
        self.restorer = RestoreEngine(orchestrator)

    def start(self):
        self.reconciler.start()
        self.transport.start(self._on_message)
        logger.info("Master node started. Waiting for workers...")
        try:
            while True:
                result = self.scheduler.dispatch_next()
                if result:
                    worker_id, job = result
                    msg = Message(type="job_assign", payload=job)
                    self.transport.send_to_worker(worker_id, msg)
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down master...")
            self.reconciler.stop()
            self.transport.stop()

    def _on_message(self, msg: Message, worker_id: str):
        if msg.type == "job_result":
            job_id = msg.payload.get("job_id")
            success = msg.payload.get("success", False)
            self.scheduler.mark_job_complete(job_id, worker_id, success)
            logger.info(f"Job result from {worker_id}: {job_id} success={success}")
        elif msg.type == "heartbeat":
            self.scheduler.heartbeat(worker_id)
        elif msg.type == "register":
            self.scheduler.register_worker(worker_id)
        else:
            logger.warning(f"Unknown message type {msg.type} from {worker_id}")

if __name__ == "__main__":
    master = MasterNode()
    master.start()