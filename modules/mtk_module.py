import os
from core.base_module import BaseModule
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                               QPushButton, QGroupBox, QGridLayout, QCheckBox,
                               QLabel, QFileDialog, QPlainTextEdit, QSplitter,
                               QInputDialog)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

class MediaTekModule(BaseModule):
    @property
    def name(self) -> str:
        return "MediaTek"

    @property
    def icon(self) -> str:
        return "📱"

    def create_ui(self, parent=None):
        self.launcher = parent
        self.main_widget = QWidget()
        main_splitter = QSplitter(Qt.Horizontal, self.main_widget)

        # LEFT PANEL
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)

        # Scatter file
        scatter_group = QGroupBox("Firmware Configuration")
        scatter_layout = QHBoxLayout(scatter_group)
        self.scatter_path = QLineEdit()
        self.scatter_path.setPlaceholderText("Select MTK scatter.txt...")
        browse_btn = QPushButton("📂 Browse")
        browse_btn.clicked.connect(self._browse_scatter)
        scatter_layout.addWidget(self.scatter_path)
        scatter_layout.addWidget(browse_btn)
        controls_layout.addWidget(scatter_group)

        # Flash Operations
        flash_group = QGroupBox("Flash Operations")
        flash_grid = QGridLayout(flash_group)
        btn_download = QPushButton("⬇️ Write Firmware")
        btn_format = QPushButton("🧹 Format / Factory Reset")
        btn_read = QPushButton("📖 Read ROM / Dump")
        btn_erase = QPushButton("❌ Erase Partition")
        btn_download.clicked.connect(lambda: self._run_mtk_command("flash"))
        btn_format.clicked.connect(lambda: self._run_mtk_command("format"))
        btn_read.clicked.connect(lambda: self._run_mtk_command("read"))
        btn_erase.clicked.connect(lambda: self._run_mtk_command("erase"))
        flash_grid.addWidget(btn_download, 0, 0)
        flash_grid.addWidget(btn_format, 0, 1)
        flash_grid.addWidget(btn_read, 1, 0)
        flash_grid.addWidget(btn_erase, 1, 1)
        controls_layout.addWidget(flash_group)

        # Security Lab
        sec_group = QGroupBox("Security & Service")
        sec_grid = QGridLayout(sec_group)
        btn_frp = QPushButton("🔒 Bypass FRP")
        btn_auth = QPushButton("🔑 Disable Auth")
        btn_bl = QPushButton("🔓 Unlock Bootloader")
        btn_frp.clicked.connect(lambda: self._run_mtk_command("frp"))
        btn_auth.clicked.connect(lambda: self._run_mtk_command("auth"))
        btn_bl.clicked.connect(lambda: self._run_mtk_command("unlock"))
        sec_grid.addWidget(btn_frp, 0, 0)
        sec_grid.addWidget(btn_auth, 0, 1)
        sec_grid.addWidget(btn_bl, 1, 0)
        controls_layout.addWidget(sec_group)

        # Options
        opt_layout = QHBoxLayout()
        self.auto_reboot = QCheckBox("Auto Reboot")
        self.auto_reboot.setChecked(True)
        opt_layout.addWidget(self.auto_reboot)
        controls_layout.addLayout(opt_layout)
        controls_layout.addStretch()

        # RIGHT PANEL
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
            self.launcher.register_active_module("MediaTek", self)

        self.log_message("MediaTek Module Ready. Load scatter file and start operations.")
        return self.main_widget

    def _browse_scatter(self):
        path, _ = QFileDialog.getOpenFileName(self.main_widget, "Select Scatter", "", "*.txt")
        if path:
            self.scatter_path.setText(path)
            self.log_message(f"Loaded: {os.path.basename(path)}")

    @Slot(str)
    def log_message(self, text):
        self.terminal.appendPlainText(text)

    def _run_mtk_command(self, operation: str):
        scatter = self.scatter_path.text()

        if operation in ("flash", "format") and not scatter:
            self.log_message("❌ Scatter file required for this operation.")
            return

        if operation == "erase":
            part, ok = QInputDialog.getText(self.main_widget, "Erase Partition", "Enter Partition Name:")
            if not ok or not part:
                return
            scatter = part

        if not hasattr(self.launcher, 'operation_manager') or self.launcher.operation_manager is None:
            self.log_message("❌ CRITICAL: Operation Manager (Engine) is offline!")
            return

        self.log_message(f"⏳ Dispatching '{operation}' to central engine queue...")

        params = {
            "sub_operation": operation,
            "scatter_path": scatter,
            "auto_reboot": self.auto_reboot.isChecked()
        }

        try:
            job_id = self.launcher.operation_manager.create_job(
                device_serial="MTK_DEVICE_BROM",
                operation="MEDIATEK_CMD",
                params=params,
                priority=2
            )
            self.log_message(f"✅ Job queued successfully! ID: {job_id}")
        except Exception as e:
            self.log_message(f"❌ Failed to queue job: {str(e)}")
