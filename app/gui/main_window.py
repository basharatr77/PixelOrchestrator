from pathlib import Path
import os
import subprocess
import sys

import app.gui.qt_bootstrap

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import ( QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QMessageBox )

from app.gui.ai.service import AIService
from app.gui.module_adapter import GUIModuleAdapter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PixelOrchestrator")
        self.resize(1280, 760)

        self.ai_service = AIService()

        self.module_adapter = GUIModuleAdapter()
        self.module_adapter.load_modules()

        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left navigation
        sidebar = QFrame()
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 24, 18, 18)
        sidebar_layout.setSpacing(10)

        title = QLabel("PIXEL\nORCHESTRATOR")
        title.setObjectName("title")
        sidebar_layout.addWidget(title)

        sidebar_layout.addSpacing(20)

        dashboard_button = QPushButton("Dashboard")
        devices_button = QPushButton("Devices")
        tools_button = QPushButton("Tools")
        ai_button = QPushButton("AI Assistant")
        database_button = QPushButton("Database")
        logs_button = QPushButton("Logs")
        settings_button = QPushButton("Settings")

        for button in [
            dashboard_button,
            devices_button,
            tools_button,
            ai_button,
            database_button,
            logs_button,
            settings_button,
        ]:
            button.setMinimumHeight(42)
            sidebar_layout.addWidget(button)

        # Windows / service shortcuts
        sidebar_layout.addSpacing(12)

        device_manager_button = QPushButton("Device Manager")
        drivers_button = QPushButton("Drivers")

        device_manager_button.setMinimumHeight(42)
        drivers_button.setMinimumHeight(42)

        sidebar_layout.addWidget(device_manager_button)
        sidebar_layout.addWidget(drivers_button)

        device_manager_button.clicked.connect(self.open_device_manager)
        drivers_button.clicked.connect(self.open_drivers_folder)
        ai_button.clicked.connect(self.open_ai_assistant)

        sidebar_layout.addStretch()

        # Main workspace
        workspace = QWidget()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(28, 24, 28, 20)
        workspace_layout.setSpacing(18)

        header = QHBoxLayout()

        heading = QLabel("AI WORKSPACE")
        heading.setObjectName("heading")

        ai_status = QLabel("● AI ONLINE")
        ai_status.setObjectName("ai_status")

        header.addWidget(heading)
        header.addStretch()
        header.addWidget(ai_status)

        workspace_layout.addLayout(header)

        ai_panel = QFrame()
        ai_panel.setObjectName("ai_panel")

        ai_layout = QVBoxLayout(ai_panel)
        ai_layout.setContentsMargins(24, 24, 24, 24)

        welcome = QLabel(
            "AI Assistant\n\n"
            "Ready to analyze devices, logs and service operations."
        )
        welcome.setObjectName("welcome")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ai_layout.addStretch()
        ai_layout.addWidget(welcome)
        ai_layout.addStretch()

        workspace_layout.addWidget(ai_panel, 1)

        status = QLabel(
            "ADB ● READY    FASTBOOT ● READY    "
            "DEVICES: 0    AI ● ONLINE    SYSTEM READY"
        )
        status.setObjectName("status")

        workspace_layout.addWidget(status)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(workspace)

        self.apply_style()

    def open_ai_assistant(self):
        """Open the AI Assistant interaction."""
        from PyQt6.QtWidgets import QInputDialog

        text, accepted = QInputDialog.getMultiLineText(
            self,
            "AI Assistant",
            "Enter device log, error, or service information:",
        )

        if not accepted:
            return

        result = self.ai_service.analyze(text)

        QMessageBox.information(
            self,
            "AI Assistant",
            result,
        )

    def open_device_manager(self):
        """Open Windows Device Manager with UAC elevation."""
        try:
            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    "Start-Process mmc.exe -ArgumentList 'devmgmt.msc' -Verb RunAs",
                ],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Device Manager",
                f"Could not open Windows Device Manager.\n\n{exc}",
            )

    def open_drivers_folder(self):
        """Open PixelOrchestrator drivers folder."""
        try:
            drivers_path = Path(__file__).resolve().parents[2] / "drivers"
            drivers_path.mkdir(parents=True, exist_ok=True)

            os.startfile(str(drivers_path))
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Drivers",
                f"Could not open the drivers folder.\n\n{exc}",
            )

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #101216;
            }

            QWidget {
                background: #101216;
                color: #E8EAED;
                font-family: "Segoe UI";
            }

            QFrame {
                background: #171A20;
            }

            QLabel#title {
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#heading {
                font-size: 24px;
                font-weight: 600;
            }

            QLabel#ai_status {
                color: #55D68A;
                font-weight: 600;
            }

            QPushButton {
                background: #1C2028;
                border: none;
                border-radius: 7px;
                padding: 10px;
                text-align: left;
                font-size: 14px;
            }

            QPushButton:hover {
                background: #272D38;
            }

            QFrame#ai_panel {
                border: 1px solid #292E38;
                border-radius: 10px;
            }

            QLabel#welcome {
                color: #9AA3B2;
                font-size: 18px;
            }

            QLabel#status {
                background: #171A20;
                border: 1px solid #292E38;
                border-radius: 7px;
                padding: 10px;
                color: #9AA3B2;
            }
        """)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
