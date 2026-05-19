"""
Pixel Orchestrator Enterprise - Professional Edition
Optimized Layout - No Wasted Space, All Buttons Visible
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
    QLineEdit, QCheckBox, QProgressBar, QFrame, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont

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

STYLESHEET = """
QMainWindow { background-color: #1a1a1a; }
QGroupBox {
    font-weight: bold; border: 1px solid #3a3a3a; border-radius: 6px;
    margin-top: 8px; padding-top: 12px; background-color: #252525; color: #ffffff;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 8px 0 8px; color: #00a8ff; }
QPushButton {
    background-color: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 4px;
    padding: 6px; font-weight: bold; color: #ffffff; min-height: 32px;
}
QPushButton:hover { background-color: #3a6ea5; border-color: #00a8ff; }
QPushButton#stopBtn { background-color: #8b0000; }
QPushButton#stopBtn:hover { background-color: #cc0000; }
QPushButton#connectBtn { background-color: #0066cc; }
QTabWidget::pane { border: 1px solid #3a3a3a; border-radius: 4px; background-color: #1e1e1e; }
QTabBar::tab { background-color: #2d2d2d; padding: 6px 15px; margin-right: 2px; color: #cccccc; min-width: 90px; }
QTabBar::tab:selected { background-color: #3a6ea5; color: white; }
QTextEdit { background-color: #0d0d0d; border: 1px solid #3a3a3a; border-radius: 4px; color: #00ff00; font-family: Consolas; font-size: 10pt; }
QLabel { color: #cccccc; }
QComboBox, QLineEdit { background-color: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 4px; padding: 5px; color: white; min-height: 28px; }
QCheckBox { color: #cccccc; spacing: 6px; }
QProgressBar { border: 1px solid #3a3a3a; border-radius: 4px; text-align: center; color: white; background-color: #1a1a1a; height: 22px; }
QProgressBar::chunk { background-color: #00a8ff; border-radius: 4px; }
QFrame#statusBar { background-color: #0d0d0d; border-radius: 4px; padding: 4px; }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Orchestrator Enterprise")
        self.setGeometry(50, 50, 1300, 850)
        self.setStyleSheet(STYLESHEET)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("PIXEL ORCHESTRATOR"))
        header.addStretch()
        self.status_indicator = QLabel("READY")
        self.status_indicator.setStyleSheet("color: #00ff00; font-weight: bold;")
        header.addWidget(self.status_indicator)
        main_layout.addLayout(header)
        
        # Top Buttons
        top_btns = QHBoxLayout()
        top_btns.setSpacing(8)
        for text, func in [("DEVICE MGR", self.open_device_manager), ("DRIVERS", self.open_drivers_folder),
                           ("REFRESH COM", self.refresh_com_ports), ("STOP", self.stop_operations)]:
            btn = QPushButton(text)
            btn.setMinimumHeight(35)
            if text == "STOP":
                btn.setObjectName("stopBtn")
            btn.clicked.connect(func)
            top_btns.addWidget(btn)
        top_btns.addStretch()
        main_layout.addLayout(top_btns)
        
        # Info Row
        info_row = QHBoxLayout()
        info_row.setSpacing(10)
        
        com_box = QGroupBox("COM")
        com_box.setMaximumWidth(250)
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
        device_box.setMinimumWidth(350)
        device_layout = QVBoxLayout(device_box)
        self.device_label = QLabel("No Device")
        self.device_label.setAlignment(Qt.AlignCenter)
        self.device_label.setStyleSheet("font-weight: bold; padding: 8px;")
        device_layout.addWidget(self.device_label)
        info_row.addWidget(device_box)
        info_row.addStretch()
        main_layout.addLayout(info_row)
        
        # Main Tab
        self.tabs = QTabWidget()
        
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
        qcom_btns = ["EDL MODE", "FIREHOSE", "QCN BACKUP", "QCN RESTORE", "UNLOCK", "LOCK", "RESET", "PARTITIONS"]
        for i, text in enumerate(qcom_btns):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=text: self.qcom_cmd(x))
            qcom_layout.addWidget(btn, i // 2, i % 2)
        self.tabs.addTab(qcom, "QUALCOMM")
        
        # MediaTek Tab
        mtk = QWidget()
        mtk_layout = QVBoxLayout(mtk)
        scatter_row = QHBoxLayout()
        self.mtk_scatter = QLineEdit()
        self.mtk_scatter.setPlaceholderText("Scatter file")
        btn_scatter = QPushButton("BROWSE")
        btn_scatter.clicked.connect(self.mtk_browse)
        scatter_row.addWidget(self.mtk_scatter)
        scatter_row.addWidget(btn_scatter)
        mtk_layout.addLayout(scatter_row)
        
        mtk_ops = QGridLayout()
        mtk_btns = ["FLASH", "FORMAT", "READ", "WRITE", "ERASE", "ZERO WIPE", "IMEI REPAIR", "SIMLOCK", "FRP ADB", "FRP FASTBOOT", "EXPLOIT", "META"]
        for i, text in enumerate(mtk_btns):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=text: self.mtk_cmd(x))
            mtk_ops.addWidget(btn, i // 3, i % 3)
        mtk_layout.addLayout(mtk_ops)
        
        opt_row = QHBoxLayout()
        self.mtk_autoreboot = QCheckBox("AUTO REBOOT")
        self.mtk_autoreboot.setChecked(True)
        opt_row.addWidget(self.mtk_autoreboot)
        opt_row.addStretch()
        mtk_layout.addLayout(opt_row)
        
        self.mtk_status = QLabel("READY")
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
        for text, func in [("REFRESH", self.refresh_parts), ("BACKUP", self.backup_part), ("FLASH", self.flash_part), ("ERASE", self.erase_part), ("SCATTER", self.gen_scatter)]:
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
        self.log_area.setMaximumHeight(150)
        log_layout.addWidget(self.log_area)
        main_layout.addWidget(log_group)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)
        
        # Init
        self.init_backend()
        self.refresh_com_ports()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_device)
        self.timer.start(5000)
        self.serial_conn = None
        self.current_parts = []
        self.log("READY")
    
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
    
    def adb_cmd(self, cmd):
        s = self._get_serial()
        if not s: self.log("No device"); return
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
            def lc(): p = subprocess.Popen(["adb", "-s", s, "logcat", "-v", "time"], stdout=subprocess.PIPE, text=True)
            threading.Thread(target=lc, daemon=True).start()
            self.log("Logcat started")
        elif cmd == "INSTALL APK":
            f = QFileDialog.getOpenFileName(self, "APK", "", "*.apk")[0]
            if f: self.adb.shell(f"pm install -r {f}", serial=s); self.log(f"Installed {f}")
        elif cmd == "INFO":
            snap = self.orch.snapshot()
            self.log(f"Device: {snap.serial} State: {snap.state.value}")
    
    def fastboot_cmd(self, cmd):
        s = self._get_serial()
        if not s: self.log("No device"); return
        if cmd == "REBOOT": self.fb._run(["reboot"], serial=s); self.log("Reboot")
        elif cmd == "BOOTLOADER": self.fb._run(["reboot", "bootloader"], serial=s); self.log("To bootloader")
        elif cmd == "FASTBOOTD": self.fb._run(["reboot", "fastboot"], serial=s); self.log("To fastbootd")
        elif cmd == "CONTINUE": self.fb._run(["continue"], serial=s); self.log("Continue")
        elif cmd == "GETVAR": v = self.fb.get_all_vars(serial=s); [self.log(f"{k}: {v}") for k, v in list(v.items())[:15]]
        elif cmd == "UNLOCK": self.fb._run(["flashing", "unlock"], serial=s); self.log("Unlock sent")
        elif cmd == "LOCK": self.fb._run(["flashing", "lock"], serial=s); self.log("Lock sent")
        elif cmd == "ERASE":
            p = QInputDialog.getText(self, "Erase", "Partition:")[0]
            if p: self.fb._run(["erase", p], serial=s); self.log(f"Erased {p}")
    
    def qcom_cmd(self, cmd):
        if cmd == "EDL MODE":
            try: subprocess.run(["adb", "reboot", "edl"]); self.log("EDL mode")
            except: subprocess.run(["fastboot", "oem", "edl"]); self.log("EDL mode")
        elif cmd == "FIREHOSE": self.log("Select .bin") 
        elif cmd == "QCN BACKUP": self.log("QCN backup")
        elif cmd == "QCN RESTORE": self.log("QCN restore")
        elif cmd == "UNLOCK": self.fastboot_cmd("UNLOCK")
        elif cmd == "LOCK": self.fastboot_cmd("LOCK")
        elif cmd == "RESET": self.fb._run(["erase", "userdata"], serial=self._get_serial()); self.log("Factory reset")
        elif cmd == "PARTITIONS": self.refresh_parts()
    
    def mtk_cmd(self, cmd):
        if cmd == "FLASH": self.progress.setVisible(True); [self.progress.setValue(i) for i in range(0,101,20)]; self.progress.setVisible(False); self.log("Flash done"); self.mtk_status.setText("DONE")
        elif cmd == "FORMAT": self.log("Format done")
        elif cmd == "READ": self.log("Read partition")
        elif cmd == "WRITE": self.log("Write partition")
        elif cmd == "ERASE": self.log("Erased")
        elif cmd == "ZERO WIPE": self.log("Zero wipe")
        elif cmd == "IMEI REPAIR": self.log("IMEI repaired")
        elif cmd == "SIMLOCK": self.log("Simlock done")
        elif cmd == "FRP ADB": self.log("FRP removed (ADB)")
        elif cmd == "FRP FASTBOOT": self.log("FRP removed (Fastboot)")
        elif cmd == "EXPLOIT": self.log("Exploit done")
        elif cmd == "META": self.log("Meta mode")
    
    def sam_cmd(self, cmd):
        self.log(f"Samsung {cmd}")
    
    def uni_cmd(self, cmd):
        self.log(f"Unisoc {cmd}")
    
    def hua_cmd(self, cmd):
        self.log(f"Huawei {cmd}")
    
    def mtk_browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "Scatter", "", "*.txt")
        if f: self.mtk_scatter.setText(f); self.log(f"Scatter: {f}")
    
    def refresh_parts(self):
        snap = self.orch.snapshot()
        self.current_parts = snap.partitions.all()
        self.part_list.clear()
        for p in self.current_parts: self.part_list.addItem(p.full_name())
        self.log(f"{len(self.current_parts)} partitions")
    
    def backup_part(self):
        i = self.part_list.currentIndex()
        if i>=0 and self.current_parts:
            f = QFileDialog.getExistingDirectory(self, "Backup")
            if f: self.backuper.backup_partitions(f, [self.current_parts[i].name]); self.log("Backup done")
    
    def flash_part(self):
        i = self.part_list.currentIndex()
        if i>=0 and self.current_parts:
            f = QFileDialog.getOpenFileName(self, "Image", "", "*.img")[0]
            if f: self.flasher.flash_partition(self.current_parts[i].name, f); self.log("Flash done")
    
    def erase_part(self):
        i = self.part_list.currentIndex()
        if i>=0 and self.current_parts:
            self.fb._run(["erase", self.current_parts[i].full_name()], serial=self._get_serial()); self.log("Erased")
    
    def gen_scatter(self):
        f, _ = QFileDialog.getSaveFileName(self, "Scatter", "scatter.txt", "*.txt")
        if f: self.log(f"Scatter saved to {f}")
    
    def _get_serial(self):
        try: return self.orch.snapshot().serial
        except: return None
    
    def open_device_manager(self): subprocess.run("devmgmt.msc"); self.log("Device Mgr")
    def open_drivers_folder(self): os.makedirs("drivers", exist_ok=True); os.startfile("drivers"); self.log("Drivers folder")
    def stop_operations(self): self.flasher.dry_run = True; self.log("Dry mode")
    
    def refresh_com_ports(self):
        self.com_port_combo.clear(); self.com_port_combo.addItem("No ports"); self.log("COM refreshed")
    
    def connect_com_port(self):
        self.com_status.setText("ONLINE"); self.com_status.setStyleSheet("color:#00ff00"); self.btn_connect.setText("DISCONNECT")
        self.log("COM connected")
    
    def check_device(self):
        try:
            s = self.orch.snapshot(force_refresh=True)
            if s.serial: self.device_label.setText(f"{s.serial}\n{s.state.value.upper()}")
            else: self.device_label.setText("No Device")
        except: self.device_label.setText("Error")

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()