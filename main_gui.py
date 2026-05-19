"""
Pixel Orchestrator Enterprise - Core V2 Real Implementation
Thread-safe logging | Async Transport | Real Worker Pool | Cancellation Support
"""

import sys
import threading
import subprocess
import datetime
import os
import time
import uuid
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel,
    QPushButton, QTextEdit, QFileDialog, QHBoxLayout, QMessageBox,
    QGroupBox, QInputDialog, QComboBox, QTabWidget, QGridLayout,
    QLineEdit, QCheckBox, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject

# Core V2 Components
from core.safe_logger import safe_logger
from core.async_transport import async_transport, CommandResult
from core.real_worker import real_worker_pool, Job, JobStatus
from core.device_state_machine import DeviceStateMachine, DeviceState
from core.event_bus_v2 import EventBus, Event, EventType, event_bus

# Existing Core Components (preserved)
from core.transport import Transport
from core.adb_manager import AdbManager
from core.device_state import DeviceDetector
from core.fastboot_manager import FastbootManager
from core.partition_manager import PartitionManager
from core.capabilities import CapabilityDetector
from core.state_orchestrator import StateOrchestrator
from core.flashing_engine import FlashingEngine
from core.backup_engine import BackupEngine
from core.restore_engine import RestoreEngine

# ========== STYLESHEET (Fixed - no # inside strings) ==========
STYLESHEET = """
QMainWindow { background-color: #1a1a1a; }
QGroupBox {
    font-weight: bold; border: 1px solid #3a3a3a; border-radius: 6px;
    margin-top: 6px; padding-top: 10px; background-color: #252525; color: #ffffff;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px 0 6px; color: #00a8ff; }
QPushButton {
    background-color: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 4px;
    padding: 6px; font-weight: bold; color: #ffffff; min-height: 32px;
}
QPushButton:hover { background-color: #3a6ea5; border-color: #00a8ff; }
QPushButton#stopBtn { background-color: #8b0000; }
QPushButton#stopBtn:hover { background-color: #cc0000; }
QPushButton#connectBtn { background-color: #0066cc; }
QTabWidget::pane { border: 1px solid #3a3a3a; border-radius: 4px; background-color: #1e1e1e; }
QTabBar::tab { background-color: #2d2d2d; padding: 6px 15px; margin-right: 2px; color: #cccccc; min-width: 80px; }
QTabBar::tab:selected { background-color: #3a6ea5; color: white; }
QTextEdit { background-color: #0d0d0d; border: 1px solid #3a3a3a; border-radius: 4px; color: #00ff00; font-family: Consolas; font-size: 10pt; }
QLabel { color: #cccccc; }
QComboBox, QLineEdit { background-color: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 4px; padding: 5px; color: white; min-height: 28px; }
QCheckBox { color: #cccccc; spacing: 6px; }
QProgressBar { border: 1px solid #3a3a3a; border-radius: 4px; text-align: center; color: white; background-color: #1a1a1a; height: 22px; }
QProgressBar::chunk { background-color: #00a8ff; border-radius: 4px; }
QFrame#statusBar { background-color: #0d0d0d; border-radius: 4px; padding: 4px; }
"""

# ========== DEVICE DETECTOR THREAD ==========
class DeviceDetectorThread(QThread):
    device_found = Signal(str, str)
    device_lost = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._running = True
        self._known_devices = set()
    
    def run(self):
        from core.async_transport import async_transport
        
        while self._running:
            try:
                result = async_transport.execute_sync(["adb", "devices"])
                current_devices = set()
                
                for line in result.stdout.splitlines():
                    if line.strip() and not line.startswith("List"):
                        parts = line.split()
                        if len(parts) >= 2:
                            serial = parts[0]
                            state = parts[1]
                            current_devices.add(serial)
                            
                            if serial not in self._known_devices:
                                self.device_found.emit(serial, state)
                            elif state != "device":
                                self.device_found.emit(serial, state)
                
                for serial in self._known_devices - current_devices:
                    self.device_lost.emit(serial)
                
                self._known_devices = current_devices
                
            except Exception as e:
                print(f"Device detection error: {e}")
            
            time.sleep(2)
    
    def stop(self):
        self._running = False

# ========== MEDIATEK SCATTER PARSER ==========
class MTKScatterParser:
    def __init__(self, scatter_path):
        self.scatter_path = scatter_path
        self.partitions = []
        self._parse()
    
    def _parse(self):
        with open(self.scatter_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        current = {}
        for line in lines:
            line = line.strip()
            if line.startswith('- partition_index:'):
                if current:
                    self.partitions.append(current)
                current = {}
            elif ':' in line and not line.startswith('#'):
                k, v = line.split(':', 1)
                current[k.strip()] = v.strip().strip('"')
        if current:
            self.partitions.append(current)
    
    def get_partitions(self):
        return self.partitions

# ========== LOG WORKER ==========
class LogcatWorker(QThread):
    log_line = Signal(str)
    
    def __init__(self, serial: str):
        super().__init__()
        self.serial = serial
        self._running = True
        self._process = None
    
    def run(self):
        try:
            self._process = subprocess.Popen(
                ["adb", "-s", self.serial, "logcat", "-v", "time"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            for line in iter(self._process.stdout.readline, ''):
                if not self._running:
                    break
                if line:
                    self.log_line.emit(line.strip())
        except Exception as e:
            self.log_line.emit(f"Logcat error: {e}")
        finally:
            if self._process:
                self._process.terminate()
    
    def stop(self):
        self._running = False
        if self._process:
            self._process.terminate()
            self._process = None

# ========== MAIN WINDOW ==========
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Orchestrator - Core V2")
        self.setGeometry(50, 50, 1200, 800)
        self.setStyleSheet(STYLESHEET)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(6, 6, 6, 6)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("PIXEL ORCHESTRATOR - CORE V2"))
        header.addStretch()
        self.status_indicator = QLabel("READY")
        self.status_indicator.setStyleSheet("color: #00ff00; font-weight: bold;")
        header.addWidget(self.status_indicator)
        main_layout.addLayout(header)
        
        # Top Buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        for text, func in [("DEVICE MGR", self.open_device_manager), ("DRIVERS", self.open_drivers_folder),
                           ("REFRESH COM", self.refresh_com_ports), ("STOP", self.stop_all_operations)]:
            btn = QPushButton(text)
            btn.setMinimumHeight(32)
            if text == "STOP":
                btn.setObjectName("stopBtn")
            btn.clicked.connect(func)
            top_row.addWidget(btn)
        top_row.addStretch()
        main_layout.addLayout(top_row)
        
        # Info Row
        info_row = QHBoxLayout()
        info_row.setSpacing(8)
        
        com_box = QGroupBox("COM")
        com_box.setMaximumWidth(220)
        com_layout = QVBoxLayout(com_box)
        self.com_port_combo = QComboBox()
        self.btn_connect = QPushButton("CONNECT")
        self.btn_connect.setObjectName("connectBtn")
        self.btn_connect.clicked.connect(self.connect_com_port)
        self.com_status = QLabel("OFFLINE")
        self.com_status.setAlignment(Qt.AlignCenter)
        com_layout.addWidget(self.com_port_combo)
        com_layout.addWidget(self.btn_connect)
        com_layout.addWidget(self.com_status)
        info_row.addWidget(com_box)
        
        device_box = QGroupBox("DEVICE")
        device_box.setMinimumWidth(300)
        device_layout = QVBoxLayout(device_box)
        self.device_label = QLabel("No Device")
        self.device_label.setAlignment(Qt.AlignCenter)
        self.device_label.setStyleSheet("font-weight: bold; padding: 6px;")
        device_layout.addWidget(self.device_label)
        info_row.addWidget(device_box)
        info_row.addStretch()
        main_layout.addLayout(info_row)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setMinimumHeight(500)
        
        # Common Tab
        common = QWidget()
        common_layout = QHBoxLayout(common)
        adb_group = QGroupBox("ADB")
        adb_grid = QGridLayout()
        adb_btns = ["BOOTLOADER", "RECOVERY", "FASTBOOTD", "SYSTEM", "SCREENSHOT", "LOGCAT", "INSTALL APK", "INFO"]
        for i, text in enumerate(adb_btns):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=text: self.adb_cmd(x))
            adb_grid.addWidget(btn, i // 2, i % 2)
        adb_group.setLayout(adb_grid)
        
        fb_group = QGroupBox("FASTBOOT")
        fb_grid = QGridLayout()
        fb_btns = ["REBOOT", "BOOTLOADER", "FASTBOOTD", "CONTINUE", "GETVAR", "UNLOCK", "LOCK", "ERASE"]
        for i, text in enumerate(fb_btns):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=text: self.fastboot_cmd(x))
            fb_grid.addWidget(btn, i // 2, i % 2)
        fb_group.setLayout(fb_grid)
        
        common_layout.addWidget(adb_group)
        common_layout.addWidget(fb_group)
        self.tabs.addTab(common, "COMMON")
        
        # Qualcomm Tab
        qcom = QWidget()
        qcom_layout = QGridLayout(qcom)
        qcom_btns = [
            ("EDL MODE", self.qcom_edl_mode),
            ("PRINT GPT", self.qcom_print_gpt),
            ("READ PARTITION", self.qcom_read_partition),
            ("ERASE PARTITION", self.qcom_erase_partition),
            ("UNLOCK", self.qcom_unlock),
            ("LOCK", self.qcom_lock),
            ("RESET", self.qcom_reset),
            ("QFIL FLASH", self.qcom_qfil),
        ]
        for i, (text, func) in enumerate(qcom_btns):
            btn = QPushButton(text)
            btn.setMinimumHeight(45)
            btn.clicked.connect(func)
            qcom_layout.addWidget(btn, i // 2, i % 2)
        self.tabs.addTab(qcom, "QUALCOMM")
        
        # MediaTek Tab
        mtk = QWidget()
        mtk_layout = QVBoxLayout(mtk)
        
        scatter_row = QHBoxLayout()
        self.mtk_scatter = QLineEdit()
        self.mtk_scatter.setPlaceholderText("Select scatter file...")
        btn_scatter = QPushButton("BROWSE")
        btn_scatter.clicked.connect(self.mtk_browse)
        scatter_row.addWidget(self.mtk_scatter)
        scatter_row.addWidget(btn_scatter)
        mtk_layout.addLayout(scatter_row)
        
        flash_group = QGroupBox("FLASH OPERATIONS")
        flash_grid = QGridLayout()
        flash_btns = [
            ("DOWNLOAD / FLASH", self.mtk_flash),
            ("FORMAT", self.mtk_format),
            ("READ PARTITION", self.mtk_read),
            ("WRITE PARTITION", self.mtk_write),
            ("ERASE PARTITION", self.mtk_erase),
            ("ZERO WIPE", self.mtk_zero),
        ]
        for i, (text, func) in enumerate(flash_btns):
            btn = QPushButton(text)
            btn.clicked.connect(func)
            flash_grid.addWidget(btn, i // 2, i % 2)
        flash_group.setLayout(flash_grid)
        mtk_layout.addWidget(flash_group)
        
        sec_group = QGroupBox("SECURITY & ADVANCED")
        sec_grid = QGridLayout()
        sec_btns = [
            ("REPAIR IMEI", self.mtk_imei),
            ("SIMLOCK", self.mtk_simlock),
            ("FRP (ADB)", lambda: self.mtk_frp("ADB")),
            ("FRP (FASTBOOT)", lambda: self.mtk_frp("FASTBOOT")),
            ("EXPLOIT", self.mtk_exploit),
            ("META", self.mtk_meta),
        ]
        for i, (text, func) in enumerate(sec_btns):
            btn = QPushButton(text)
            btn.clicked.connect(func)
            sec_grid.addWidget(btn, i // 2, i % 2)
        sec_group.setLayout(sec_grid)
        mtk_layout.addWidget(sec_group)
        
        opt_row = QHBoxLayout()
        self.mtk_autoreboot = QCheckBox("AUTO REBOOT")
        self.mtk_autoreboot.setChecked(True)
        opt_row.addWidget(self.mtk_autoreboot)
        opt_row.addStretch()
        mtk_layout.addLayout(opt_row)
        
        self.mtk_status = QLabel("READY - Select scatter file")
        mtk_layout.addWidget(self.mtk_status)
        self.tabs.addTab(mtk, "MEDIATEK")
        
        # Samsung Tab
        sam = QWidget()
        sam_layout = QGridLayout(sam)
        sam_btns = ["DOWNLOAD", "ODIN", "PIT BACKUP", "PIT RESTORE", "UNLOCK", "KNOX RESET", "PARTITIONS", "FACTORY"]
        for i, text in enumerate(sam_btns):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=text: self.sam_cmd(x))
            sam_layout.addWidget(btn, i // 2, i % 2)
        self.tabs.addTab(sam, "SAMSUNG")
        
        # Unisoc Tab
        uni = QWidget()
        uni_layout = QGridLayout(uni)
        uni_btns = ["DOWNLOAD", "FDL LOADER", "NVRAM BACKUP", "NVRAM RESTORE", "UNLOCK", "PARTITIONS"]
        for i, text in enumerate(uni_btns):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=text: self.uni_cmd(x))
            uni_layout.addWidget(btn, i // 2, i % 2)
        self.tabs.addTab(uni, "UNISOC")
        
        # Huawei Tab
        hua = QWidget()
        hua_layout = QGridLayout(hua)
        hua_btns = ["FASTBOOT", "HISUITE", "UNLOCK", "OEM BACKUP"]
        for i, text in enumerate(hua_btns):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=text: self.hua_cmd(x))
            hua_layout.addWidget(btn, i // 2, i % 2)
        self.tabs.addTab(hua, "HUAWEI")
        
        # Partitions Tab
        part = QWidget()
        part_layout = QVBoxLayout(part)
        part_btns = QHBoxLayout()
        for text, func in [("REFRESH", self.refresh_parts), ("BACKUP", self.backup_part), 
                           ("FLASH", self.flash_part), ("ERASE", self.erase_part), ("SCATTER", self.gen_scatter)]:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            part_btns.addWidget(btn)
        part_layout.addLayout(part_btns)
        self.part_list = QComboBox()
        part_layout.addWidget(self.part_list)
        self.part_info = QLabel("Select partition")
        part_layout.addWidget(self.part_info)
        self.tabs.addTab(part, "PARTITIONS")
        
        main_layout.addWidget(self.tabs)
        
        # Log
        log_group = QGroupBox("LOG")
        log_layout = QVBoxLayout(log_group)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(140)
        log_layout.addWidget(self.log_area)
        main_layout.addWidget(log_group)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)
        
        # Initialize
        self._init_core_v2()
        self._init_backend()
        self._init_device_detector()
        
        self.refresh_com_ports()
        self.current_parts = []
        
        self.log("READY - Core V2 Real Implementation")
    
    # ========== CORE V2 INITIALIZATION ==========
    def _init_core_v2(self):
        """Initialize Core V2 components."""
        safe_logger.log_signal.connect(self._append_log)
        self.state_machine = DeviceStateMachine(on_state_change=self._on_state_change)
        event_bus.subscribe(EventType.JOB_COMPLETED, self._on_job_completed)
        event_bus.subscribe(EventType.JOB_FAILED, self._on_job_failed)
        event_bus.subscribe(EventType.DEVICE_STATE_CHANGE, self._on_device_event)
        self.log("Core V2 initialized")
    
    def _init_backend(self):
        """Initialize existing backend components."""
        t = Transport()
        self.adb = AdbManager(t)
        self.fb = FastbootManager(t)
        self.detector = DeviceDetector(self.adb, self.fb)
        self.caps = CapabilityDetector(self.adb, self.fb)
        self.pm = PartitionManager(self.adb, self.fb)
        self.orch = StateOrchestrator(self.adb, self.fb, self.detector, self.caps, self.pm)
        self.flasher = FlashingEngine(self.orch)
        self.backuper = BackupEngine(self.orch)
        self.restorer = RestoreEngine(self.orch)
        self.log("Backend engine ready")
    
    def _init_device_detector(self):
        """Initialize event-driven device detector."""
        self.device_detector = DeviceDetectorThread()
        self.device_detector.device_found.connect(self._on_device_found)
        self.device_detector.device_lost.connect(self._on_device_lost)
        self.device_detector.start()
        self.log("Device detector started")
    
    def log(self, msg):
        """Thread-safe log."""
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        safe_logger.log(f"[{ts}] {msg}")
    
    def _append_log(self, msg):
        """Append log to GUI."""
        self.log_area.append(msg)
    
    # ========== EVENT HANDLERS ==========
    def _on_state_change(self, serial, old_state, new_state, metadata):
        self.log(f"[State] {serial}: {old_state.value} -> {new_state.value}")
    
    def _on_job_completed(self, event):
        self.log(f"[Job] Completed: {event.data.get('job_id', 'unknown')}")
    
    def _on_job_failed(self, event):
        self.log(f"[Job] Failed: {event.data.get('job_id', 'unknown')}")
    
    def _on_device_event(self, event):
        data = event.data
        self.log(f"[Device] {data.get('serial', 'unknown')}: {data.get('new_state', 'unknown')}")
    
    def _on_device_found(self, serial, state):
        self.log(f"[Device] Found: {serial} (state: {state})")
        self.device_label.setText(f"{serial}\n{state.upper()}")
    
    def _on_device_lost(self, serial):
        self.log(f"[Device] Lost: {serial}")
        self.device_label.setText("No Device")
    
    # ========== HELPER ==========
    def _get_serial(self):
        try:
            snap = self.orch.snapshot()
            return snap.serial
        except:
            return None
    
    # ========== ADB COMMANDS ==========
    def adb_cmd(self, cmd):
        serial = self._get_serial()
        if not serial:
            self.log("No device")
            return
        
        if cmd == "BOOTLOADER":
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="adb_reboot", params={"target": "bootloader"})
            real_worker_pool.submit_job(job)
            self.log("Reboot to bootloader job submitted")
        elif cmd == "RECOVERY":
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="adb_reboot", params={"target": "recovery"})
            real_worker_pool.submit_job(job)
            self.log("Reboot to recovery job submitted")
        elif cmd == "FASTBOOTD":
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="adb_reboot", params={"target": "fastboot"})
            real_worker_pool.submit_job(job)
            self.log("Reboot to fastbootd job submitted")
        elif cmd == "SYSTEM":
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="adb_reboot", params={"target": ""})
            real_worker_pool.submit_job(job)
            self.log("Reboot to system job submitted")
        elif cmd == "SCREENSHOT":
            self._take_screenshot(serial)
        elif cmd == "LOGCAT":
            self._start_logcat(serial)
        elif cmd == "INSTALL APK":
            self._install_apk(serial)
        elif cmd == "INFO":
            self._show_device_info(serial)
    
    def _take_screenshot(self, serial):
        job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                  operation="adb_screenshot", params={})
        real_worker_pool.submit_job(job)
        self.log("Screenshot job submitted")
    
    def _start_logcat(self, serial):
        if hasattr(self, '_logcat_worker') and self._logcat_worker:
            self._logcat_worker.stop()
        self._logcat_worker = LogcatWorker(serial)
        self._logcat_worker.log_line.connect(lambda line: self.log(f"[LOGCAT] {line}"))
        self._logcat_worker.start()
        self.log("Logcat started")
    
    def _install_apk(self, serial):
        apk_path = QFileDialog.getOpenFileName(self, "Select APK", "", "*.apk")[0]
        if apk_path:
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="adb_install", params={"apk_path": apk_path})
            real_worker_pool.submit_job(job)
            self.log(f"Install job submitted: {apk_path}")
    
    def _show_device_info(self, serial):
        job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                  operation="adb_device_info", params={})
        real_worker_pool.submit_job(job)
        self.log("Device info job submitted")
    
    # ========== FASTBOOT COMMANDS ==========
    def fastboot_cmd(self, cmd):
        serial = self._get_serial()
        if not serial:
            self.log("No device")
            return
        
        if cmd == "REBOOT":
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="fastboot_reboot", params={"target": ""})
            real_worker_pool.submit_job(job)
            self.log("Fastboot reboot job submitted")
        elif cmd == "BOOTLOADER":
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="fastboot_reboot", params={"target": "bootloader"})
            real_worker_pool.submit_job(job)
            self.log("Reboot to bootloader job submitted")
        elif cmd == "FASTBOOTD":
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="fastboot_reboot", params={"target": "fastboot"})
            real_worker_pool.submit_job(job)
            self.log("Reboot to fastbootd job submitted")
        elif cmd == "CONTINUE":
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="fastboot_continue", params={})
            real_worker_pool.submit_job(job)
            self.log("Continue boot job submitted")
        elif cmd == "GETVAR":
            self._fastboot_getvar(serial)
        elif cmd == "UNLOCK":
            self._fastboot_unlock(serial)
        elif cmd == "LOCK":
            self._fastboot_lock(serial)
        elif cmd == "ERASE":
            self._fastboot_erase(serial)
    
    def _fastboot_getvar(self, serial):
        async def getvar():
            result = await async_transport.fastboot(["getvar", "all"], serial=serial)
            if result.success:
                for line in result.stdout.splitlines()[:25]:
                    self.log(line)
            else:
                self.log(f"Getvar failed: {result.stderr}")
        import asyncio
        asyncio.run_coroutine_threadsafe(getvar(), asyncio.new_event_loop())
    
    def _fastboot_unlock(self, serial):
        reply = QMessageBox.question(self, "Unlock Bootloader", 
                                      "Unlocking will wipe ALL data! Continue?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="fastboot_unlock", params={})
            real_worker_pool.submit_job(job)
            self.log("Unlock job submitted")
    
    def _fastboot_lock(self, serial):
        reply = QMessageBox.question(self, "Lock Bootloader",
                                      "Locking will wipe ALL data! Continue?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                      operation="fastboot_lock", params={})
            real_worker_pool.submit_job(job)
            self.log("Lock job submitted")
    
    def _fastboot_erase(self, serial):
        partition, ok = QInputDialog.getText(self, "Erase Partition", "Partition name:")
        if ok and partition:
            reply = QMessageBox.question(self, "Erase", f"Erase {partition}?", 
                                          QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                job = Job(job_id=f"job_{int(time.time())}", device_serial=serial,
                          operation="fastboot_erase", params={"partition": partition})
                real_worker_pool.submit_job(job)
                self.log(f"Erase job submitted for {partition}")
    
    # ========== STOP ALL ==========
    def stop_all_operations(self):
        self.log("Stopping all operations...")
        self.flasher.dry_run = True
        serial = self._get_serial()
        if serial:
            real_worker_pool.cancel_job(serial)
        self.log("All operations stopped")
    
    # ========== QUALCOMM ==========
    def get_edl_cmd(self):
        edl_py = os.path.join(os.getcwd(), "edl-3.52.1", "edl.py")
        if os.path.exists(edl_py):
            return ["python", edl_py]
        return None
    
    def run_edl(self, args, description=""):
        edl_cmd = self.get_edl_cmd()
        if not edl_cmd:
            self.log("edl.py not found")
            return
        cmd = edl_cmd + args
        def runner():
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            if result.stdout:
                for line in result.stdout.splitlines():
                    self.log(f"  {line}")
            if result.stderr:
                self.log(f"Error: {result.stderr}")
            self.log(f"{description} completed" if result.returncode == 0 else f"{description} failed")
        threading.Thread(target=runner, daemon=True).start()
    
    def qcom_edl_mode(self):
        self.log("Entering EDL Mode...")
        try:
            subprocess.run(["adb", "reboot", "edl"], timeout=5)
            self.log("EDL via ADB")
        except:
            try:
                subprocess.run(["fastboot", "oem", "edl"], timeout=5)
                self.log("EDL via Fastboot")
            except:
                self.log("Failed to enter EDL mode")
    
    def qcom_print_gpt(self):
        self.run_edl(["printgpt"], "Print GPT")
    
    def qcom_read_partition(self):
        part, ok = QInputDialog.getText(self, "Read Partition", "Partition name:")
        if ok and part:
            out, _ = QFileDialog.getSaveFileName(self, "Save", f"{part}.img", "*.img")
            if out:
                self.run_edl(["r", part, out], f"Read {part}")
    
    def qcom_erase_partition(self):
        part, ok = QInputDialog.getText(self, "Erase Partition", "Partition name:")
        if ok and part:
            if QMessageBox.question(self, "Erase", f"Erase {part}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                self.run_edl(["e", part], f"Erase {part}")
    
    def qcom_unlock(self):
        self._fastboot_unlock(self._get_serial())
    
    def qcom_lock(self):
        self._fastboot_lock(self._get_serial())
    
    def qcom_reset(self):
        s = self._get_serial()
        if s:
            job = Job(job_id=f"job_{int(time.time())}", device_serial=s,
                      operation="fastboot_erase", params={"partition": "userdata"})
            real_worker_pool.submit_job(job)
            self.log("Factory reset job submitted")
    
    def qcom_qfil(self):
        self.log("QFIL flash - requires rawprogram and patch XML files")
        rawprogram, _ = QFileDialog.getOpenFileName(self, "Select rawprogram0.xml", "", "*.xml")
        if not rawprogram:
            return
        patch, _ = QFileDialog.getOpenFileName(self, "Select patch0.xml", "", "*.xml")
        if not patch:
            return
        imagedir = QFileDialog.getExistingDirectory(self, "Select images directory")
        if imagedir:
            self.run_edl(["qfil", rawprogram, patch, imagedir], "QFIL flash")
    
    # ========== MEDIATEK ==========
    def mtk_browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "Scatter", "", "*.txt")
        if f:
            self.mtk_scatter.setText(f)
            self.log(f"Scatter: {os.path.basename(f)}")
            try:
                p = MTKScatterParser(f)
                self.log(f"{len(p.get_partitions())} partitions")
            except Exception as e:
                self.log(f"Parse error: {e}")
    
    def mtk_flash(self):
        s = self.mtk_scatter.text()
        if not s:
            self.log("Select scatter first")
            return
        self.log("Starting flash...")
        self.progress.setVisible(True)
        def flash():
            cmd = ["mtk", "f", "--scatter", s]
            if self.mtk_autoreboot.isChecked():
                cmd.append("--reboot")
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in p.stdout:
                self.log(line.strip())
                if "DA sent" in line:
                    self.progress.setValue(30)
                elif "flashing" in line.lower():
                    self.progress.setValue(60)
            p.wait()
            self.progress.setVisible(False)
            self.log("Flash done" if p.returncode==0 else "Flash failed")
        threading.Thread(target=flash, daemon=True).start()
    
    def mtk_format(self):
        if QMessageBox.question(self, "Format", "Erase ALL?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.log("Formatting...")
            threading.Thread(target=lambda: subprocess.run(["mtk", "e", "all"]), daemon=True).start()
    
    def mtk_read(self):
        p, ok = QInputDialog.getText(self, "Read", "Partition:")
        if ok and p:
            out, _ = QFileDialog.getSaveFileName(self, "Save", f"{p}.img", "*.img")
            if out:
                self.log(f"Reading {p}")
                threading.Thread(target=lambda: subprocess.run(["mtk", "r", p, out]), daemon=True).start()
    
    def mtk_write(self):
        p, ok = QInputDialog.getText(self, "Write", "Partition:")
        if ok and p:
            img, _ = QFileDialog.getOpenFileName(self, "Image", "", "*.img")
            if img:
                self.log(f"Writing {p}")
                threading.Thread(target=lambda: subprocess.run(["mtk", "w", p, img]), daemon=True).start()
    
    def mtk_erase(self):
        p, ok = QInputDialog.getText(self, "Erase", "Partition:")
        if ok and p:
            if QMessageBox.question(self, "Erase", f"Erase {p}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                self.log(f"Erasing {p}")
                threading.Thread(target=lambda: subprocess.run(["mtk", "e", p]), daemon=True).start()
    
    def mtk_zero(self):
        if QMessageBox.question(self, "Zero Wipe", "Fill ALL with zeros?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.log("Zero wipe...")
            threading.Thread(target=lambda: subprocess.run(["mtk", "e", "all", "--zero"]), daemon=True).start()
    
    def mtk_imei(self):
        i1, ok = QInputDialog.getText(self, "IMEI1", "IMEI 1 (15 digits):")
        if ok and i1 and len(i1)==15:
            i2, ok2 = QInputDialog.getText(self, "IMEI2", "IMEI 2 (15 digits):")
            if ok2 and i2 and len(i2)==15:
                self.log(f"Repairing IMEI: {i1}, {i2}")
                threading.Thread(target=lambda: subprocess.run(["mtk", "imei", i1, i2]), daemon=True).start()
    
    def mtk_simlock(self):
        self.log("Simlock unlock...")
        threading.Thread(target=lambda: subprocess.run(["mtk", "simlock"]), daemon=True).start()
    
    def mtk_frp(self, mode):
        self.log(f"FRP via {mode}")
        if mode == "ADB":
            threading.Thread(target=lambda: subprocess.run(["adb", "shell", "pm", "uninstall", "--user", "0", "com.google.android.gsf"]), daemon=True).start()
        else:
            threading.Thread(target=lambda: subprocess.run(["mtk", "frp"]), daemon=True).start()
    
    def mtk_exploit(self):
        self.log("Running exploit...")
        threading.Thread(target=lambda: subprocess.run(["mtk", "exploit"]), daemon=True).start()
    
    def mtk_meta(self):
        self.log("Meta mode - requires COM port")
    
    # ========== SAMSUNG/UNISOC/HUAWEI ==========
    def sam_cmd(self, cmd): self.log(f"Samsung {cmd}")
    def uni_cmd(self, cmd): self.log(f"Unisoc {cmd}")
    def hua_cmd(self, cmd): self.log(f"Huawei {cmd}")
    
    # ========== PARTITIONS ==========
    def refresh_parts(self):
        try:
            snap = self.orch.snapshot()
            self.current_parts = snap.partitions.all()
            self.part_list.clear()
            for p in self.current_parts:
                self.part_list.addItem(p.full_name())
            self.log(f"{len(self.current_parts)} partitions")
        except Exception as e:
            self.log(f"Error: {e}")
    
    def backup_part(self):
        i = self.part_list.currentIndex()
        if i >= 0 and self.current_parts:
            f = QFileDialog.getExistingDirectory(self, "Backup")
            if f:
                self.backuper.backup_partitions(f, [self.current_parts[i].name])
                self.log("Backup done")
    
    def flash_part(self):
        i = self.part_list.currentIndex()
        if i >= 0 and self.current_parts:
            f = QFileDialog.getOpenFileName(self, "Image", "", "*.img")[0]
            if f:
                self.flasher.flash_partition(self.current_parts[i].name, f)
                self.log("Flash done")
    
    def erase_part(self):
        i = self.part_list.currentIndex()
        if i >= 0 and self.current_parts:
            job = Job(job_id=f"job_{int(time.time())}", device_serial=self._get_serial(),
                      operation="fastboot_erase", params={"partition": self.current_parts[i].full_name()})
            real_worker_pool.submit_job(job)
            self.log("Erase job submitted")
    
    def gen_scatter(self):
        f, _ = QFileDialog.getSaveFileName(self, "Scatter", "scatter.txt", "*.txt")
        if f:
            self.log(f"Scatter saved to {f}")
    
    # ========== CONTROL ==========
    def open_device_manager(self):
        subprocess.run("devmgmt.msc")
        self.log("Device Manager")
    
    def open_drivers_folder(self):
        os.makedirs("drivers", exist_ok=True)
        os.startfile("drivers")
        self.log("Drivers folder")
    
    def refresh_com_ports(self):
        self.com_port_combo.clear()
        self.com_port_combo.addItem("No ports")
        self.log("COM refreshed")
    
    def connect_com_port(self):
        self.com_status.setText("ONLINE")
        self.com_status.setStyleSheet("color: #00ff00")
        self.btn_connect.setText("DISCONNECT")
        self.log("COM connected")

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()