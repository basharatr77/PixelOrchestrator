from core.logger import log_event
async def _handle_qualcomm_job_async(self, job: Job):
    params = job.params
    op = params.get("sub_operation")
    programmer = params.get("programmer_path", "")
    output_file = params.get("output_file", "")
    partition = params.get("partition_name", "")
    rawprogram = params.get("rawprogram", "")
    patch = params.get("patch", "")
    imagedir = params.get("imagedir", "")
    qcn_file = params.get("qcn_file", "")

    # Build command using python edl.py (from edl-3.52.1 folder)
    edl_py = os.path.join(os.getcwd(), "edl-3.52.1", "edl.py")
    if not os.path.exists(edl_py):
        await self.update_job_status(job.id, "FAILED", error="edl.py not found")
        return False

    cmd = ["python", edl_py]

    if op == "edl":
        # Just reboot to EDL (already handled by UI; here we just succeed)
        await self.update_job_status(job.id, "COMPLETED", result="EDL mode triggered")
        return True

    elif op == "printgpt":
        cmd.append("printgpt")
    elif op == "firehose" and programmer:
        cmd.extend(["--loader", programmer])
    elif op == "read" and partition and output_file:
        cmd.extend(["r", partition, output_file])
    elif op == "erase" and partition:
        cmd.extend(["e", partition])
    elif op == "qfil" and rawprogram and patch and imagedir:
        cmd.extend(["qfil", rawprogram, patch, imagedir])
    elif op == "qcn_backup" and output_file:
        cmd.extend(["--genqcn", output_file])
    elif op == "qcn_restore" and qcn_file:
        cmd.extend(["--restoreqcn", qcn_file])
    elif op == "unlock":
        cmd = ["fastboot", "flashing", "unlock"]
    elif op == "lock":
        cmd = ["fastboot", "flashing", "lock"]
    elif op == "reset":
        cmd = ["fastboot", "erase", "userdata"]
    elif op == "info":
        cmd.append("--info")
    else:
        await self.update_job_status(job.id, "FAILED", error=f"Unknown Qualcomm op: {op}")
        return False

    await self.update_job_status(job.id, "RUNNING")
    log_event(job.device_serial, f"qcom_{op}", "INFO", f"Starting Qualcomm operation: {op}")

    def stream_to_ui(line_text):
        if self.launcher and hasattr(self.launcher, "active_modules") and "Qualcomm" in self.launcher.active_modules:
            ui_module = self.launcher.active_modules["Qualcomm"]
            QMetaObject.invokeMethod(ui_module, "log_message", Qt.QueuedConnection, Q_ARG(str, line_text))

    try:
        result = await async_transport_v2.execute_command_async(cmd, job_id=job.id, log_callback=stream_to_ui)
        if result.success:
            await self.update_job_status(job.id, "COMPLETED", result=result.stdout)
            log_event(job.device_serial, f"qcom_{op}", "INFO", "Operation completed")
            return True
        else:
            await self.update_job_status(job.id, "FAILED", error=result.stderr)
            log_event(job.device_serial, f"qcom_{op}", "ERROR", result.stderr)
            return False
    except Exception as e:
        await self.update_job_status(job.id, "FAILED", error=str(e))
        log_event(job.device_serial, f"qcom_{op}", "ERROR", str(e))
        return False
    def update_job_checkpoint(self, job_id: str, checkpoint: dict):
        """Store checkpoint data for a job (e.g., last flashed partition)."""
        if job_id in self._jobs:
            job = self._jobs[job_id]
            if "checkpoint" not in job.params:
                job.params["checkpoint"] = {}
            job.params["checkpoint"].update(checkpoint)
            self._save_job(job)
            log_event(job.device_serial, "checkpoint", "INFO", f"Checkpoint saved: {checkpoint}")

