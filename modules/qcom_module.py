import os
from core.base_module import BaseModule
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                               QPushButton, QGroupBox, QGridLayout, QCheckBox,
                               QLabel, QFileDialog, QPlainTextEdit, QSplitter,
                               QInputDialog)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

class QualcommModule(BaseModule):
    @property
    def name(self) -> str:
        return "Qualcomm"

    @property
    def icon(self) -> str:
        return "🐚"

    def create_ui(self, parent=None):
        self.launcher = parent
        self.main_widget = QWidget()
        main_splitter = QSplitter(Qt.Horizontal, self.main_widget)

        # LEFT PANEL
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)

        # Programmer / Firehose file
        prog_group = QGroupBox("Programmer / Firehose")
        prog_layout = QHBoxLayout(prog_group)
        self.prog_path = QLineEdit()
        self.prog_path.setPlaceholderText("Select Firehose programmer .bin file...")
        browse_prog = QPushButton("📂 Browse")
        browse_prog.clicked.connect(self._browse_programmer)
        prog_layout.addWidget(self.prog_path)
        prog_layout.addWidget(browse_prog)
        controls_layout.addWidget(prog_group)

        # Flash Operations
        flash_group = QGroupBox("Flash Operations")
        flash_grid = QGridLayout(flash_group)
        btn_edl = QPushButton("🔴 Enter EDL Mode")
        btn_printgpt = QPushButton("📋 Print GPT")
        btn_firehose = QPushButton("🔥 Load Firehose")
        btn_read = QPushButton("📖 Read Partition")
        btn_erase = QPushButton("❌ Erase Partition")
        btn_qfil = QPushButton("📦 QFIL Flash")
        btn_reset = QPushButton("🔄 Factory Reset")
        btn_info = QPushButton("ℹ️ Device Info")

        btn_edl.clicked.connect(lambda: self._dispatch("edl"))
        btn_printgpt.clicked.connect(lambda: self._dispatch("printgpt"))
        btn_firehose.clicked.connect(lambda: self._dispatch("firehose"))
        btn_read.clicked.connect(lambda: self._dispatch("read"))
        btn_erase.clicked.connect(lambda: self._dispatch("erase"))
        btn_qfil.clicked.connect(lambda: self._dispatch("qfil"))
        btn_reset.clicked.connect(lambda: self._dispatch("reset"))
        btn_info.clicked.connect(lambda: self._dispatch("info"))

        flash_grid.addWidget(btn_edl, 0, 0)
        flash_grid.addWidget(btn_printgpt, 0, 1)
        flash_grid.addWidget(btn_firehose, 1, 0)
        flash_grid.addWidget(btn_read, 1, 1)
        flash_grid.addWidget(btn_erase, 2, 0)
        flash_grid.addWidget(btn_qfil, 2, 1)
        flash_grid.addWidget(btn_reset, 3, 0)
        flash_grid.addWidget(btn_info, 3, 1)
        controls_layout.addWidget(flash_group)

        # Security
        sec_group = QGroupBox("Security & Unlock")
        sec_grid = QGridLayout(sec_group)
        btn_unlock = QPushButton("🔓 Unlock Bootloader")
        btn_lock = QPushButton("🔒 Lock Bootloader")
        btn_qcn_backup = QPushButton("💾 Backup QCN")
        btn_qcn_restore = QPushButton("💾 Restore QCN")
        btn_unlock.clicked.connect(lambda: self._dispatch("unlock"))
        btn_lock.clicked.connect(lambda: self._dispatch("lock"))
        btn_qcn_backup.clicked.connect(lambda: self._dispatch("qcn_backup"))
        btn_qcn_restore.clicked.connect(lambda: self._dispatch("qcn_restore"))
        sec_grid.addWidget(btn_unlock, 0, 0)
        sec_grid.addWidget(btn_lock, 0, 1)
        sec_grid.addWidget(btn_qcn_backup, 1, 0)
        sec_grid.addWidget(btn_qcn_restore, 1, 1)
        controls_layout.addWidget(sec_group)

        controls_layout.addStretch()

        # RIGHT PANEL: Terminal
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 10))
        self.terminal.setStyleSheet("background-color: #121212; color: #00ff00;")
        log_layout.addWidget(self.terminal)

        main_splitter.addWidget(controls_widget)
        main_splitter.addWidget(log_widget)
        main_splitter.setSizes([480, 420])

        outer = QVBoxLayout(self.main_widget)
        outer.addWidget(main_splitter)

        if hasattr(self.launcher, "register_active_module"):
            self.launcher.register_active_module("Qualcomm", self)

        self.log_message("Qualcomm Module Ready. Load programmer file and start operations.")
        return self.main_widget

    def _browse_programmer(self):
        path, _ = QFileDialog.getOpenFileName(self.main_widget, "Select Firehose Programmer", "", "*.bin")
        if path:
            self.prog_path.setText(path)
            self.log_message(f"Loaded programmer: {os.path.basename(path)}")

    @Slot(str)
    def log_message(self, text):
        self.terminal.appendPlainText(text)

    def _dispatch(self, operation):
        if not hasattr(self.launcher, 'operation_manager') or self.launcher.operation_manager is None:
            self.log_message("❌ Operation Manager not available!")
            return

        programmer = self.prog_path.text()
        if operation in ("firehose", "qfil") and not programmer:
            self.log_message("❌ Programmer file required for this operation.")
            return

        params = {
            "sub_operation": operation,
            "programmer_path": programmer,
            "auto_reboot": False   # Qualcomm may not need auto reboot flag
        }

        # For erase, ask partition name
        if operation == "erase":
            part, ok = QInputDialog.getText(self.main_widget, "Erase Partition", "Enter Partition Name:")
            if not ok or not part:
                return
            params["partition_name"] = part
        elif operation == "read":
            part, ok = QInputDialog.getText(self.main_widget, "Read Partition", "Partition Name:")
            if not ok or not part:
                return
            out, _ = QFileDialog.getSaveFileName(self.main_widget, "Save Image", f"{part}.img", "*.img")
            if not out:
                return
            params["partition_name"] = part
            params["output_file"] = out
        elif operation == "qfil":
            rawprogram, _ = QFileDialog.getOpenFileName(self.main_widget, "Select rawprogram0.xml", "", "*.xml")
            if not rawprogram:
                return
            patch, _ = QFileDialog.getOpenFileName(self.main_widget, "Select patch0.xml", "", "*.xml")
            if not patch:
                return
            imagedir = QFileDialog.getExistingDirectory(self.main_widget, "Select images directory")
            if not imagedir:
                return
            params["rawprogram"] = rawprogram
            params["patch"] = patch
            params["imagedir"] = imagedir
        elif operation == "qcn_backup":
            out, _ = QFileDialog.getSaveFileName(self.main_widget, "Save QCN Backup", "qcn_backup.qcn", "*.qcn")
            if not out:
                return
            params["output_file"] = out
        elif operation == "qcn_restore":
            qcn, _ = QFileDialog.getOpenFileName(self.main_widget, "Select QCN File", "", "*.qcn")
            if not qcn:
                return
            params["qcn_file"] = qcn

        self.log_message(f"⏳ Dispatching '{operation}' to engine queue...")

        try:
            job_id = self.launcher.operation_manager.create_job(
                device_serial="QCOM_DEVICE_EDL",
                operation="QUALCOMM_CMD",
                params=params,
                priority=2
            )
            self.log_message(f"✅ Job queued! ID: {job_id}")
        except Exception as e:
            self.log_message(f"❌ Failed: {e}")
