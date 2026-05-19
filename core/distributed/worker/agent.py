import asyncio
import json
import logging
from core.distributed.common.message import Message
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

logger = logging.getLogger(__name__)

class WorkerAgent:
    def __init__(self, worker_id: str, master_url: str, shared_secret: str = ""):
        self.worker_id = worker_id
        self.master_url = master_url
        self.secret = shared_secret
        self._stop = False
        self._init_local_engines()

    def _init_local_engines(self):
        transport = Transport()
        self.adb = AdbManager(transport)
        self.fastboot = FastbootManager(transport)
        self.detector = DeviceDetector(self.adb, self.fastboot)
        self.caps = CapabilityDetector(self.adb, self.fastboot)
        self.part_mgr = PartitionManager(self.adb, self.fastboot)
        self.orchestrator = StateOrchestrator(self.adb, self.fastboot, self.detector, self.caps, self.part_mgr)
        self.flasher = FlashingEngine(self.orchestrator)
        self.backuper = BackupEngine(self.orchestrator)
        self.restorer = RestoreEngine(self.orchestrator)

    async def connect_async(self):
        import websockets
        while not self._stop:
            try:
                async with websockets.connect(self.master_url) as ws:
                    reg = Message(type="register", payload={"worker_id": self.worker_id})
                    await ws.send(json.dumps(reg.to_dict()))
                    raw = await ws.recv()
                    ack = Message.from_dict(json.loads(raw))
                    if ack.type != "ack":
                        logger.error("Registration failed")
                        continue
                    logger.info("✅ Registered with master")
                    heartbeat_task = asyncio.create_task(self._send_heartbeat(ws))
                    try:
                        async for raw in ws:
                            msg = Message.from_dict(json.loads(raw))
                            if msg.type == "job_assign":
                                await self._execute_job(msg.payload, ws)
                    finally:
                        heartbeat_task.cancel()
            except Exception as e:
                logger.error(f"Connection error: {e}, retrying in 5s")
                await asyncio.sleep(5)

    def connect(self):
        asyncio.run(self.connect_async())

    async def _send_heartbeat(self, ws):
        while not self._stop:
            await asyncio.sleep(10)
            hb = Message(type="heartbeat", payload={"worker_id": self.worker_id})
            await ws.send(json.dumps(hb.to_dict()))

    async def _execute_job(self, job: dict, ws):
        job_id = job.get("job_id")
        job_type = job.get("type", "flash")
        logger.info(f"Executing job {job_id} of type {job_type}")
        result_payload = {"job_id": job_id, "success": False}
        try:
            if job_type == "flash":
                partition = job.get("partition")
                image = job.get("image_path")
                slot = job.get("slot")
                op = self.flasher.flash_partition(partition, image, slot=slot)
                result_payload["success"] = op.success
                result_payload["message"] = op.message
            elif job_type == "backup":
                output_dir = job.get("output_dir")
                partitions = job.get("partitions")
                items = self.backuper.backup_partitions(output_dir, partitions)
                result_payload["success"] = True
                result_payload["items"] = [{"full_name": i.full_name, "size": i.size} for i in items]
            elif job_type == "restore":
                manifest = job.get("manifest")
                res = self.restorer.restore_from_manifest(manifest)
                result_payload["success"] = len(res.failed) == 0
                result_payload["restored"] = res.restored
            else:
                result_payload["error"] = f"Unknown job type {job_type}"
        except Exception as e:
            result_payload["error"] = str(e)
            result_payload["success"] = False
        result_msg = Message(type="job_result", payload=result_payload)
        await ws.send(json.dumps(result_msg.to_dict()))
        logger.info(f"Job {job_id} finished")

def start_worker(worker_id: str, master_url: str, secret: str = ""):
    agent = WorkerAgent(worker_id, master_url, secret)
    agent.connect()