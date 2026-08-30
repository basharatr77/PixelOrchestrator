from pathlib import Path
import os
import subprocess
import sys

import app.gui.qt_bootstrap

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import ( QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QMessageBox, QScrollArea )

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

        # Dynamic module/action workspace.
        self.module_scroll = QScrollArea()
        self.module_scroll.setWidgetResizable(True)
        self.module_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.module_container = QWidget()
        self.module_layout = QVBoxLayout(self.module_container)
        self.module_layout.setContentsMargins(0, 0, 0, 0)
        self.module_layout.setSpacing(12)

        self.module_scroll.setWidget(self.module_container)
        workspace_layout.addWidget(self.module_scroll, 1)

        self.refresh_module_action_ui()

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

    def refresh_module_action_ui(self):
        """Rebuild the dynamic module/action workspace from the adapter."""

        while self.module_layout.count():
            item = self.module_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        module_title = QLabel("MODULE ACTIONS")
        module_title.setObjectName("module_title")
        self.module_layout.addWidget(module_title)

        self.module_action_buttons = {}

        for module in self.module_adapter.get_modules():
            module_id = module["id"]

            module_frame = QFrame()
            module_frame.setObjectName("module_frame")

            module_box = QVBoxLayout(module_frame)
            module_box.setContentsMargins(16, 14, 16, 14)
            module_box.setSpacing(8)

            module_label = QLabel(
                f"{module['name']}    {module['type']}    v{module['version']}"
            )
            module_label.setObjectName("module_label")
            module_box.addWidget(module_label)

            self.module_action_buttons[module_id] = {}

            for action in self.module_adapter.get_action_buttons(module_id):
                action_id = action["id"]

                button = QPushButton(action["name"])
                button.setEnabled(bool(action["enabled"]))
                button.setToolTip(
                    action.get("description")
                    or action.get("capability_id", "")
                )

                button.clicked.connect(
                    lambda checked=False,
                    mid=module_id,
                    aid=action_id:
                    self.execute_module_action(mid, aid)
                )

                module_box.addWidget(button)
                self.module_action_buttons[module_id][action_id] = button

            self.module_layout.addWidget(module_frame)

        self.module_layout.addStretch()

    def execute_module_action(self, module_id, action_id):
        """Execute a dynamically rendered module action."""
        try:
            module = self.module_adapter.registry.get(module_id)

            if module is None:
                raise ValueError(f"Module not found: {module_id}")

            action = next(
                (
                    item
                    for item in module.get_actions()
                    if item.id == action_id
                ),
                None,
            )

            if action is None:
                raise ValueError(
                    f"Action not found: {module_id}:{action_id}"
                )

            if getattr(action, "dangerous", False):
                confirmation = QMessageBox.question(
                    self,
                    "Confirm Dangerous Action",
                    (
                        f"Are you sure you want to execute "
                        f"'{action.name}'?\n\n"
                        "This action is marked as dangerous."
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if confirmation != QMessageBox.StandardButton.Yes:
                    return

            result = self.module_adapter.execute_action(
                module_id,
                action_id,
            )

            message = getattr(result, "message", None) or str(result)

            if getattr(result, "success", True):
                QMessageBox.information(
                    self,
                    "Module Action",
                    message,
                )
            else:
                QMessageBox.warning(
                    self,
                    "Module Action",
                    message,
                )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Module Action Error",
                str(exc),
            )

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

            QLabel#module_title {
    font-size: 16px;
    font-weight: 700;
    padding: 4px 0;
}

QFrame#module_frame {
    padding: 4px;
}

QLabel#module_label {
    font-size: 14px;
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
