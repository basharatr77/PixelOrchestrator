"""
Pixel Orchestrator Enterprise - Complete Toolkit
Includes ADB/Fastboot utilities, flashing, backup, restore, and advanced features
"""

import sys
import threading
import subprocess
import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel,
    QPushButton, QTextEdit, QFileDialog, QHBoxLayout, QMessageBox,
    QGroupBox, QInputDialog
)
from PySide6.QtCore import Qt, QTimer

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Orchestrator Enterprise - Complete Toolkit")
        self.resize(1300, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Device info label
        self.device_label = QLabel("No device detected")
        self.device_label.setStyleSheet("font-weight: bold; padding: 10px; background-color: #2d2d2d; border-radius: 5px;")
        main_layout.addWidget(self.device_label)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("font-family: Consolas; font-size: 10pt;")
        main_layout.addWidget(self.log_area)
        
        # ========== ADB UTILITIES SECTION ==========
        adb_group = QGroupBox("ADB Utilities (when device in ADB mode)")
        adb_layout = QHBoxLayout()
        
        self.btn_adb_reboot_bootloader = QPushButton("Reboot to Bootloader")
        self.btn_adb_reboot_bootloader.clicked.connect(self.adb_reboot_bootloader)
        self.btn_adb_reboot_recovery = QPushButton("Reboot to Recovery")
        self.btn_adb_reboot_recovery.clicked.connect(self.adb_reboot_recovery)
        self.btn_adb_reboot_fastbootd = QPushButton("Reboot to Fastbootd")
        self.btn_adb_reboot_fastbootd.clicked.connect(self.adb_reboot_fastbootd)
        self.btn_adb_reboot_system = QPushButton("Reboot to System")
        self.btn_adb_reboot_system.clicked.connect(self.adb_reboot_system)
        self.btn_adb_screenshot = QPushButton("Take Screenshot")
        self.btn_adb_screenshot.clicked.connect(self.adb_screenshot)
        self.btn_adb_logcat = QPushButton("Start Logcat")
        self.btn_adb_logcat.clicked.connect(self.adb_logcat)
        self.btn_adb_install_apk = QPushButton("Install APK")
        self.btn_adb_install_apk.clicked.connect(self.adb_install_apk)
        
        adb_layout.addWidget(self.btn_adb_reboot_bootloader)
        adb_layout.addWidget(self.btn_adb_reboot_recovery)
        adb_layout.addWidget(self.btn_adb_reboot_fastbootd)
        adb_layout.addWidget(self.btn_adb_reboot_system)
        adb_layout.addWidget(self.btn_adb_screenshot)
        adb_layout.addWidget(self.btn_adb_logcat)
        adb_layout.addWidget(self.btn_adb_install_apk)
        adb_group.setLayout(adb_layout)
        main_layout.addWidget(adb_group)
        
        # ========== FASTBOOT UTILITIES SECTION ==========
        fastboot_group = QGroupBox("Fastboot Utilities (when device in Fastboot/Fastbootd mode)")
        fastboot_layout = QHBoxLayout()
        
        self.btn_fb_reboot = QPushButton("Reboot Device")
        self.btn_fb_reboot.clicked.connect(self.fastboot_reboot)
        self.btn_fb_reboot_bootloader = QPushButton("Reboot to Bootloader")
        self.btn_fb_reboot_bootloader.clicked.connect(self.fastboot_reboot_bootloader)
        self.btn_fb_reboot_fastbootd = QPushButton("Reboot to Fastbootd")
        self.btn_fb_reboot_fastbootd.clicked.connect(self.fastboot_reboot_fastbootd)
        self.btn_fb_continue = QPushButton("Continue Boot")
        self.btn_fb_continue.clicked.connect(self.fastboot_continue)
        self.btn_fb_getvar = QPushButton("Get All Vars")
        self.btn_fb_getvar.clicked.connect(self.fastboot_getvar)
        self.btn_fb_unlock = QPushButton("Unlock Bootloader")
        self.btn_fb_unlock.clicked.connect(self.fastboot_unlock)
        self.btn_fb_lock = QPushButton("Lock Bootloader")
        self.btn_fb_lock.clicked.connect(self.fastboot_lock)
        self.btn_fb_erase = QPushButton("Erase Partition")
        self.btn_fb_erase.clicked.connect(self.fastboot_erase)
        
        fastboot_layout.addWidget(self.btn_fb_reboot)
        fastboot_layout.addWidget(self.btn_fb_reboot_bootloader)
        fastboot_layout.addWidget(self.btn_fb_reboot_fastbootd)
        fastboot_layout.addWidget(self.btn_fb_continue)
        fastboot_layout.addWidget(self.btn_fb_getvar)
        fastboot_layout.addWidget(self.btn_fb_unlock)
        fastboot_layout.addWidget(self.btn_fb_lock)
        fastboot_layout.addWidget(self.btn_fb_erase)
        fastboot_group.setLayout(fastboot_layout)
        main_layout.addWidget(fastboot_group)
        
        # ========== FLASHING & BACKUP SECTION ==========
        ops_group = QGroupBox("Device Operations")
        ops_layout = QHBoxLayout()
        
        self.btn_check = QPushButton("Check Device")
        self.btn_check.clicked.connect(self.check_device)
        self.btn_backup = QPushButton("Backup Boot")
        self.btn_backup.clicked.connect(self.backup_boot)
        self.btn_flash = QPushButton("Flash Boot")
        self.btn_flash.clicked.connect(self.flash_boot)
        self.btn_restore = QPushButton("Restore from Manifest")
        self.btn_restore.clicked.connect(self.restore_device)
        
        ops_layout.addWidget(self.btn_check)
        ops_layout.addWidget(self.btn_backup)
        ops_layout.addWidget(self.btn_flash)
        ops_layout.addWidget(self.btn_restore)
        ops_group.setLayout(ops_layout)
        main_layout.addWidget(ops_group)
        
        # Initialize backend
        self.init_backend()
        
        # Auto-refresh timer (every 5 seconds)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_device)
        self.timer.start(5000)
        
        self.logcat_process = None
    
    def init_backend(self):
        """Initialize all backend components."""
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
        self.log("Backend initialized successfully")
    
    def log(self, message: str):
        """Add message to log area."""
        self.log_area.append(message)
        print(message)
    
    def check_device(self):
        """Check and display device status."""
        try:
            snap = self.orchestrator.snapshot(force_refresh=True)
            if snap.serial:
                self.device_label.setText(
                    f"📱 Device: {snap.serial}\n"
                    f"⚡ State: {snap.state.value}\n"
                    f"🔧 Capabilities: A/B={snap.capabilities.ab_slots}, "
                    f"Dynamic={snap.capabilities.dynamic_partitions}, "
                    f"Tensor={snap.capabilities.tensor}"
                )
                self.log(f"[{snap.state.value}] Device {snap.serial}")
            else:
                self.device_label.setText("📱 No device detected")
        except Exception as e:
            self.log(f"Device check error: {e}")
    
    # ========== ADB Utility Methods ==========
    def _get_serial(self):
        try:
            snap = self.orchestrator.snapshot()
            return snap.serial
        except:
            return None
    
    def adb_reboot_bootloader(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in ADB mode")
            return
        self.log(f"Rebooting {serial} to bootloader...")
        self.adb.reboot("bootloader", serial=serial)
        self.log("Reboot command sent")
    
    def adb_reboot_recovery(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in ADB mode")
            return
        self.log(f"Rebooting {serial} to recovery...")
        self.adb.reboot("recovery", serial=serial)
        self.log("Reboot command sent")
    
    def adb_reboot_fastbootd(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in ADB mode")
            return
        self.log(f"Rebooting {serial} to fastbootd...")
        self.adb.reboot("fastboot", serial=serial)
        self.log("Reboot command sent")
    
    def adb_reboot_system(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in ADB mode")
            return
        self.log(f"Rebooting {serial} to system...")
        self.adb.reboot("", serial=serial)
        self.log("Reboot command sent")
    
    def adb_screenshot(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in ADB mode")
            return
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.log(f"Taking screenshot on {serial} -> {filename}")
        result = self.adb.shell("screencap /sdcard/screenshot.png", serial=serial)
        if result.success:
            self.adb.pull("/sdcard/screenshot.png", filename, serial=serial)
            self.adb.shell("rm /sdcard/screenshot.png", serial=serial)
            self.log(f"Screenshot saved to {filename}")
        else:
            self.log("Screenshot failed (device may not support screencap)")
    
    def adb_logcat(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in ADB mode")
            return
        if self.logcat_process and self.logcat_process.poll() is None:
            self.log("Logcat already running. Close the terminal window to stop.")
            return
        self.log("Starting logcat... (will stream to log area)")
        def worker():
            cmd = ["adb", "-s", serial, "logcat", "-v", "threadtime"]
            self.logcat_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            for line in iter(self.logcat_process.stdout.readline, ''):
                if line:
                    self.log(f"[LOGCAT] {line.strip()}")
        t = threading.Thread(target=worker, daemon=True)
        t.start()
    
    def adb_install_apk(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in ADB mode")
            return
        apk_path = QFileDialog.getOpenFileName(self, "Select APK file", "", "APK files (*.apk)")[0]
        if not apk_path:
            return
        self.log(f"Installing {apk_path} on {serial}...")
        result = self.adb.shell(f"pm install -r \"{apk_path}\"", serial=serial, timeout=120)
        if result.success:
            self.log("APK installed successfully")
        else:
            self.log(f"Installation failed: {result.stderr}")
    
    # ========== Fastboot Utility Methods ==========
    def fastboot_reboot(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in fastboot mode")
            return
        self.log(f"Rebooting device {serial}...")
        result = self.fastboot._run(["reboot"], serial=serial)
        self.log(f"Reboot command sent: {result.success}")
    
    def fastboot_reboot_bootloader(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in fastboot mode")
            return
        self.log(f"Rebooting {serial} to bootloader...")
        result = self.fastboot._run(["reboot", "bootloader"], serial=serial)
        self.log(f"Reboot command sent: {result.success}")
    
    def fastboot_reboot_fastbootd(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in fastboot mode")
            return
        self.log(f"Rebooting {serial} to fastbootd...")
        result = self.fastboot._run(["reboot", "fastboot"], serial=serial)
        self.log(f"Reboot command sent: {result.success}")
    
    def fastboot_continue(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in fastboot mode")
            return
        self.log(f"Continuing boot on {serial}...")
        result = self.fastboot._run(["continue"], serial=serial)
        self.log(f"Continue command sent: {result.success}")
    
    def fastboot_getvar(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in fastboot mode")
            return
        self.log("Fetching fastboot variables...")
        vars_dict = self.fastboot.get_all_vars(serial=serial)
        self.log("Fastboot variables:")
        for key, value in list(vars_dict.items())[:20]:
            self.log(f"  {key}: {value}")
        if len(vars_dict) > 20:
            self.log(f"  ... and {len(vars_dict)-20} more")
    
    def fastboot_unlock(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in fastboot mode")
            return
        reply = QMessageBox.question(
            self, "Confirm Unlock",
            "WARNING: Unlocking bootloader will wipe all user data and void warranty.\n\nAre you absolutely sure?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self.log(f"Attempting to unlock bootloader on {serial}...")
        result = self.fastboot._run(["flashing", "unlock"], serial=serial, timeout=30)
        if result.success:
            self.log("Unlock command sent. Device may show a confirmation screen.")
        else:
            self.log(f"Unlock failed: {result.stderr}")
    
    def fastboot_lock(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in fastboot mode")
            return
        reply = QMessageBox.question(
            self, "Confirm Lock",
            "WARNING: Locking bootloader will wipe all user data.\n\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self.log(f"Attempting to lock bootloader on {serial}...")
        result = self.fastboot._run(["flashing", "lock"], serial=serial, timeout=30)
        if result.success:
            self.log("Lock command sent. Device may show a confirmation screen.")
        else:
            self.log(f"Lock failed: {result.stderr}")
    
    def fastboot_erase(self):
        serial = self._get_serial()
        if not serial:
            self.log("No device in fastboot mode")
            return
        partition, ok = QInputDialog.getText(self, "Erase Partition", "Enter partition name (e.g., userdata, cache):")
        if not ok or not partition.strip():
            return
        reply = QMessageBox.question(
            self, "Confirm Erase",
            f"WARNING: Erasing partition '{partition}' will delete data.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self.log(f"Erasing partition {partition} on {serial}...")
        result = self.fastboot._run(["erase", partition], serial=serial, timeout=60)
        if result.success:
            self.log(f"Partition {partition} erased successfully.")
        else:
            self.log(f"Erase failed: {result.stderr}")
    
    # ========== Backup/Flash/Restore Methods ==========
    def backup_boot(self):
        folder = QFileDialog.getExistingDirectory(self, "Select backup folder")
        if not folder:
            return
        def log_cb(msg):
            self.log(msg)
        try:
            self.log("Starting boot partition backup...")
            results = self.backuper.backup_partitions(folder, ["boot"], log_callback=log_cb)
            for r in results:
                self.log(f"Backup saved: {r.full_name} -> {r.image_path} (SHA256: {r.sha256[:16]}...)")
            QMessageBox.information(self, "Backup Complete", f"Backup saved to {folder}")
        except Exception as e:
            self.log(f"Backup error: {e}")
            QMessageBox.critical(self, "Backup Failed", str(e))
    
    def flash_boot(self):
        path = QFileDialog.getOpenFileName(self, "Select boot image", "", "Image files (*.img)")[0]
        if not path:
            return
        reply = QMessageBox.question(
            self, "Confirm Flash",
            f"Are you sure you want to flash {path} to boot partition?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        def log_cb(msg):
            self.log(msg)
        try:
            self.log(f"Flashing {path}...")
            result = self.flasher.flash_partition("boot", path, log_callback=log_cb)
            if result.success:
                QMessageBox.information(self, "Flash Complete", result.message)
            else:
                QMessageBox.critical(self, "Flash Failed", result.message)
            self.log(f"Flash result: {result.message}")
        except Exception as e:
            self.log(f"Flash error: {e}")
            QMessageBox.critical(self, "Flash Error", str(e))
    
    def restore_device(self):
        manifest = QFileDialog.getOpenFileName(self, "Select backup manifest", "", "JSON files (*.json)")[0]
        if not manifest:
            return
        reply = QMessageBox.question(
            self, "Confirm Restore",
            "This will restore partitions from the selected backup. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.log(f"Restoring from {manifest}...")
            result = self.restorer.restore_from_manifest(manifest)
            self.log(f"Restored: {result.restored}, Failed: {result.failed}")
            QMessageBox.information(self, "Restore Complete", f"Restored: {len(result.restored)}\nFailed: {len(result.failed)}")
        except Exception as e:
            self.log(f"Restore error: {e}")
            QMessageBox.critical(self, "Restore Failed", str(e))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()