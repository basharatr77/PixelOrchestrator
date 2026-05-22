import sys
import asyncio
import qasync
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGridLayout, QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout)
from PySide6.QtCore import Qt

from core.hwid import verify_hwid, register_hwid
from core.module_loader import discover_modules
from core.operation_manager import OperationManager
from core.event_bus import event_bus
from core.logger import log_event

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Orchestrator v2 - Professional Edition")
        self.setGeometry(100, 100, 1000, 700)

        if not verify_hwid():
            reply = QMessageBox.question(self, "Activation Required",
                "Hardware ID not registered. Activate this PC?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                register_hwid()
                QMessageBox.information(self, "Success", "PC Activated! Please restart the tool.")
            sys.exit(0)

        self.modules = discover_modules()
        self.active_modules = {}
        self.operation_manager = OperationManager(launcher=self)
        self.operation_manager.start()
        self.operation_manager.register_handler("MEDIATEK_CMD", self.operation_manager._handle_mediatek_job_sync)
        self.operation_manager.register_handler("QUALCOMM_CMD", self.operation_manager._handle_qualcomm_job_sync)

        self.setup_ui()
        log_event("system", "launcher", "INFO", "Launcher started successfully")

    def register_active_module(self, name, module_instance):
        self.active_modules[name] = module_instance

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.stacked_widget = QStackedWidget()
        self.active_modules_map = {}

        dashboard = QWidget()
        dash_layout = QVBoxLayout(dashboard)
        title = QLabel("PIXEL ORCHESTRATOR DASHBOARD")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #3a6ea5; margin: 20px;")
        dash_layout.addWidget(title, alignment=Qt.AlignCenter)

        grid = QGridLayout()
        for idx, module in enumerate(self.modules):
            btn = QPushButton(f"{module.icon} {module.name} Module")
            btn.setFixedSize(200, 100)
            btn.setStyleSheet("font-size: 14px; font-weight: bold; border-radius: 10px; background-color: #2b2b2b;")
            btn.clicked.connect(lambda checked, m=module: self.switch_to_module(m))
            grid.addWidget(btn, idx // 3, idx % 3)
        dash_layout.addLayout(grid)
        dash_layout.addStretch()
        self.stacked_widget.addWidget(dashboard)
        main_layout.addWidget(self.stacked_widget)

        self.status_label = QLabel("System Ready | Secured via HWID")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        main_layout.addWidget(self.status_label)

    def switch_to_module(self, module):
        if module.name not in self.active_modules_map:
            workspace_wrapper = QWidget()
            wrapper_layout = QVBoxLayout(workspace_wrapper)

            top_bar = QHBoxLayout()
            home_btn = QPushButton("🏠 Return to Dashboard")
            home_btn.setStyleSheet("background-color: #c0392b; padding: 5px 15px; font-weight: bold;")
            home_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

            mod_title = QLabel(f"Active Workspace: {module.name}")
            mod_title.setStyleSheet("font-weight: bold; font-size: 16px;")

            top_bar.addWidget(home_btn)
            top_bar.addWidget(mod_title, alignment=Qt.AlignRight)
            wrapper_layout.addLayout(top_bar)

            actual_ui = module.create_ui(self)
            wrapper_layout.addWidget(actual_ui)

            new_index = self.stacked_widget.addWidget(workspace_wrapper)
            self.active_modules_map[module.name] = new_index

        self.stacked_widget.setCurrentIndex(self.active_modules_map[module.name])
        self.status_label.setText(f"Active Session: {module.name} Module running...")

async def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Start event bus as an asyncio task (now in the same loop as Qt)
    asyncio.create_task(event_bus.start())

    window = LauncherWindow()
    window.show()

    # Keep Qt event loop running
    await asyncio.get_running_loop().run_in_executor(None, app.exec)

if __name__ == "__main__":
    qasync.run(main())