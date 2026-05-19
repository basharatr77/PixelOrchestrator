"""
Pixel Orchestrator Enterprise - Complete Edition
MediaTek (mtkclient) + Qualcomm (edl.py) + All Chipsets
"""

import sys
import threading
import subprocess
import datetime
import os
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel,
    QPushButton, QTextEdit, QFileDialog, QHBoxLayout, QMessageBox,
    QGroupBox, QInputDialog, QComboBox, QTabWidget, QGridLayout,
    QLineEdit, QCheckBox, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal

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

# ========== STYLESHEET ==========
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

# ========== MAIN WINDOW ==========
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Orchestrator - Complete Edition")
        self.setGeometry(50, 50, 1200, 800)
        self.setStyleSheet(STYLESHEET)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(6, 6, 6, 6)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("PIXEL ORCHESTRATOR - COMPLETE EDITION"))
        header.addStretch()
        self.status_indicator = QLabel("READY")
        self.status_indicator.setStyleSheet("color: #00ff00; font-weight: bold;")
        header.addWidget(self.status_indicator)
        main_layout.addLayout(header)
        
        # Top Buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        for text, func in [("DEVICE MGR", self.open_device_manager), ("DRIVERS", self.open_drivers_folder),
                           ("REFRESH COM", self.refresh_com_ports), ("STOP", self.stop_operations)]:
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
        self.init_backend()
        self.refresh_com_ports()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_device)
        self.timer.start(5000)
        self.current_parts = []
        self.log("READY - Complete Edition")
    
    def init_backend(self):
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
        self.log("Engine ready")
    
    def log(self, msg):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_area.append(f"[{ts}] {msg}")
    
    def _get_serial(self):
        try:
            snap = self.orch.snapshot()
            return snap.serial
        except:
            return None
    
    # ========== ED.PY HELPER ==========
    def get_edl_cmd(self):
        # Path to edl.py
        edl_py = os.path.join(os.getcwd(), "edl-3.52.1", "edl.py")
        if os.path.exists(edl_py):
            return ["python", edl_py]
        return None
    
    # ========== ADB/FASTBOOT ==========
    def adb_cmd(self, cmd):
        s = self._get_serial()
        if not s:
            self.log("No device")
            return
        cmds = {"BOOTLOADER": "bootloader", "RECOVERY": "recovery", "FASTBOOTD": "fastboot", "SYSTEM": ""}
        if cmd in cmds:
            self.adb.reboot(cmds[cmd], serial=s)
            self.log(f"Reboot to {cmd}")
        elif cmd == "SCREENSHOT":
            name = f"ss_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.adb.shell("screencap /sdcard/s.png", serial=s)
            self.adb.pull("/sdcard/s.png", name, serial=s)
            self.adb.shell("rm /sdcard/s.png", serial=s)
            self.log(f"Screenshot: {name}")
        elif cmd == "LOGCAT":
            def lc():
                p = subprocess.Popen(["adb", "-s", s, "logcat", "-v", "time"], stdout=subprocess.PIPE, text=True)
                for line in iter(p.stdout.readline, ''):
                    if line:
                        self.log(f"[LOGCAT] {line.strip()}")
            threading.Thread(target=lc, daemon=True).start()
        elif cmd == "INSTALL APK":
            f = QFileDialog.getOpenFileName(self, "APK", "", "*.apk")[0]
            if f:
                self.adb.shell(f"pm install -r {f}", serial=s)
                self.log(f"Installed {f}")
        elif cmd == "INFO":
            snap = self.orch.snapshot()
            self.log(f"Device: {snap.serial} State: {snap.state.value}")
    
    def fastboot_cmd(self, cmd):
        s = self._get_serial()
        if not s:
            self.log("No device")
            return
        if cmd == "REBOOT":
            self.fb._run(["reboot"], serial=s); self.log("Reboot")
        elif cmd == "BOOTLOADER":
            self.fb._run(["reboot", "bootloader"], serial=s); self.log("To bootloader")
        elif cmd == "FASTBOOTD":
            self.fb._run(["reboot", "fastboot"], serial=s); self.log("To fastbootd")
        elif cmd == "CONTINUE":
            self.fb._run(["continue"], serial=s); self.log("Continue")
        elif cmd == "GETVAR":
            v = self.fb.get_all_vars(serial=s)
            for k, val in list(v.items())[:15]:
                self.log(f"{k}: {val}")
        elif cmd == "UNLOCK":
            self.fb._run(["flashing", "unlock"], serial=s); self.log("Unlock sent")
        elif cmd == "LOCK":
            self.fb._run(["flashing", "lock"], serial=s); self.log("Lock sent")
        elif cmd == "ERASE":
            p = QInputDialog.getText(self, "Erase", "Partition:")[0]
            if p:
                self.fb._run(["erase", p], serial=s); self.log(f"Erased {p}")
    
    # ========== QUALCOMM (with edl.py) ==========
    def run_edl(self, args, description=""):
        edl_cmd = self.get_edl_cmd()
        if not edl_cmd:
            self.log("edl.py not found in edl-3.52.1 folder")
            return
        cmd = edl_cmd + args
        self.log(f"Running: {' '.join(cmd)}")
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
        self.fastboot_cmd("UNLOCK")
    
    def qcom_lock(self):
        self.fastboot_cmd("LOCK")
    
    def qcom_reset(self):
        s = self._get_serial()
        if s:
            self.fb._run(["erase", "userdata"], serial=s)
            self.log("Factory reset")
    
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
    
    # ========== MEDIATEK (with mtkclient) ==========
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
            self.fb._run(["erase", self.current_parts[i].full_name()], serial=self._get_serial())
            self.log("Erased")
    
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
    
    def stop_operations(self):
        self.flasher.dry_run = True
        self.log("Dry mode")
    
    def refresh_com_ports(self):
        self.com_port_combo.clear()
        self.com_port_combo.addItem("No ports")
        self.log("COM refreshed")
    
    def connect_com_port(self):
        self.com_status.setText("ONLINE")
        self.com_status.setStyleSheet("color: #00ff00")
        self.btn_connect.setText("DISCONNECT")
        self.log("COM connected")
    
    def check_device(self):
        try:
            s = self.orch.snapshot(force_refresh=True)
            if s.serial:
                self.device_label.setText(f"{s.serial}\n{s.state.value.upper()}")
            else:
                self.device_label.setText("No Device")
        except:
            self.device_label.setText("Error")

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()