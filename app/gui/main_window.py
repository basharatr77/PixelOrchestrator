from pathlib import Path
import os
import subprocess
import sys

import app.gui.qt_bootstrap

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import ( QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QMessageBox, QScrollArea, QLineEdit, QGridLayout, QComboBox, QPlainTextEdit )

from app.gui.ai.service import AIService
from app.gui.module_adapter import GUIModuleAdapter


class MainWindow(QMainWindow):
    def __init__(self, device_registry=None):
        super().__init__()

        self.setWindowTitle("PixelOrchestrator")
        self.resize(1280, 760)

        self.ai_service = AIService()

        self.module_adapter = GUIModuleAdapter()
        self.device_registry = device_registry
        self.selected_device_id = None
        self.device_details = QLabel('No device selected.')
        self.device_details.setObjectName('device_details')
        self.device_model = QLabel("Model: Unknown")
        self.device_serial = QLabel("Serial: Unknown")
        self.device_state = QLabel("State: Unknown")
        self.device_transport = QLabel("Transport: Unknown")
        self.device_module_type = QLabel("Module: Unknown")
        self.device_brand = QLabel("Brand: Unknown")
        self.device_android_version = QLabel("Android: Unknown")
        self.device_selector = QComboBox()
        self.device_selector.currentIndexChanged.connect(self._on_device_selected)
        self._populate_device_selector()
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
        dashboard_button.clicked.connect(self.open_dashboard)
        devices_button.clicked.connect(self.open_devices)
        tools_button.clicked.connect(self.open_tools)
        database_button.clicked.connect(self.open_database)
        logs_button.clicked.connect(self.open_logs)
        settings_button.clicked.connect(self.open_settings)

        sidebar_layout.addStretch()

        # Main workspace
        workspace = QWidget()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(28, 24, 28, 20)
        workspace_layout.setSpacing(18)

        self.dashboard_workspace = QFrame()
        self.dashboard_workspace.setObjectName("dashboard_workspace")
        dashboard_layout = QVBoxLayout(self.dashboard_workspace)
        dashboard_layout.setContentsMargins(16, 14, 16, 14)

        dashboard_title = QLabel("Dashboard")
        dashboard_title.setObjectName("workspace_title")
        dashboard_layout.addWidget(dashboard_title)

        dashboard_placeholder = QLabel(
            "Dashboard workspace is ready. Device operations are available from Devices."
        )
        dashboard_layout.addWidget(dashboard_placeholder)
        dashboard_layout.addStretch()

        workspace_layout.addWidget(self.dashboard_workspace, 1)

        self.logs_workspace = QFrame()
        self.logs_workspace.setObjectName("logs_workspace")
        logs_layout = QVBoxLayout(self.logs_workspace)
        logs_layout.setContentsMargins(16, 14, 16, 14)

        logs_title = QLabel("Logs")
        logs_title.setObjectName("workspace_title")
        logs_layout.addWidget(logs_title)

        logs_placeholder = QLabel(
            "Logs workspace is ready. Event log display will be added separately."
        )
        logs_layout.addWidget(logs_placeholder)
        logs_layout.addStretch()

        workspace_layout.addWidget(self.logs_workspace, 1)

        header = QHBoxLayout()

        heading = QLabel("AI WORKSPACE")
        heading.setObjectName("heading")

        ai_status = QLabel("● AI ONLINE")
        ai_status.setObjectName("ai_status")

        header.addWidget(heading)
        header.addStretch()
        header.addWidget(self.device_selector)
        header.addWidget(ai_status)

        workspace_layout.addLayout(header)

        self.device_workspace = QFrame()
        self.device_workspace.setObjectName("device_workspace")
        device_workspace_layout = QVBoxLayout(self.device_workspace)
        device_workspace_layout.setContentsMargins(16, 14, 16, 14)
        device_workspace_layout.addWidget(self.device_details)

        self.device_identity_group = QFrame()
        self.device_identity_group.setObjectName("device_identity_group")
        device_identity_layout = QVBoxLayout(self.device_identity_group)
        device_identity_layout.setContentsMargins(0, 0, 0, 0)
        self.device_identity_heading = QLabel("Device Identity")
        self.device_identity_heading.setObjectName("device_identity_heading")
        device_identity_layout.addWidget(self.device_identity_heading)
        device_identity_layout.addWidget(self.device_model)
        device_identity_layout.addWidget(self.device_serial)
        device_workspace_layout.addWidget(self.device_identity_group)

        self.device_connection_group = QFrame()
        self.device_connection_group.setObjectName("device_connection_group")
        device_connection_layout = QVBoxLayout(self.device_connection_group)
        device_connection_layout.setContentsMargins(0, 0, 0, 0)
        device_connection_layout.addWidget(self.device_state)
        device_connection_layout.addWidget(self.device_transport)
        device_connection_layout.addWidget(self.device_module_type)
        device_workspace_layout.addWidget(self.device_connection_group)

        self.device_metadata_group = QFrame()
        self.device_metadata_group.setObjectName("device_metadata_group")
        device_metadata_layout = QVBoxLayout(self.device_metadata_group)
        device_metadata_layout.setContentsMargins(0, 0, 0, 0)
        device_metadata_layout.addWidget(self.device_brand)
        device_metadata_layout.addWidget(self.device_android_version)
        device_workspace_layout.addWidget(self.device_metadata_group)

        self.device_operations_group = QFrame()
        self.device_operations_group.setObjectName("device_operations_group")
        device_operations_layout = QVBoxLayout(self.device_operations_group)
        device_operations_layout.setContentsMargins(0, 0, 0, 0)

        # Dynamic module/action workspace.
        self.operations_panel = QFrame()
        self.operations_panel.setObjectName("operations_panel")
        operations_layout = QVBoxLayout(self.operations_panel)
        operations_layout.setContentsMargins(16, 14, 16, 14)

        self.operation_result = QFrame()
        self.operation_result.setObjectName("operation_result")
        operation_result_layout = QVBoxLayout(self.operation_result)
        operation_result_layout.setContentsMargins(12, 10, 12, 10)

        self.operation_result_heading = QLabel("Operation Result")
        self.operation_result_heading.setObjectName("operation_result_heading")
        operation_result_layout.addWidget(self.operation_result_heading)

        self.operation_result_device = QLabel("Device: -")
        self.operation_result_device.setObjectName("operation_result_device")
        operation_result_layout.addWidget(self.operation_result_device)

        self.operation_result_operation = QLabel("Operation: -")
        self.operation_result_operation.setObjectName("operation_result_operation")
        operation_result_layout.addWidget(self.operation_result_operation)

        self.operation_result_status = QLabel("Status: -")
        self.operation_result_status.setObjectName("operation_result_status")
        operation_result_layout.addWidget(self.operation_result_status)

        self.operation_result_message = QLabel("Message: -")
        self.operation_result_message.setObjectName("operation_result_message")
        self.operation_result_message.setWordWrap(True)
        operation_result_layout.addWidget(self.operation_result_message)

        self.operation_result_details = QPlainTextEdit()
        self.operation_result_details.setObjectName("operation_result_details")
        self.operation_result_details.setReadOnly(True)
        self.operation_result_details.setPlaceholderText(
            "Operation details will appear here."
        )
        self.operation_result_details.setMaximumHeight(120)
        operation_result_layout.addWidget(self.operation_result_details)

        operations_layout.addWidget(self.operation_result)

        self.module_scroll = QScrollArea()
        self.module_scroll.setWidgetResizable(True)
        self.module_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.module_container = QWidget()
        self.module_layout = QVBoxLayout(self.module_container)
        self.module_layout.setContentsMargins(0, 0, 0, 0)
        self.module_layout.setSpacing(12)

        self.module_scroll.setWidget(self.module_container)
        operations_layout.addWidget(self.module_scroll)
        device_operations_layout.addWidget(self.operations_panel)
        device_workspace_layout.addWidget(self.device_operations_group, 1)
        workspace_layout.addWidget(self.device_workspace, 1)

        self._workspaces = {
            "dashboard": self.dashboard_workspace,
            "devices": self.device_workspace,
            "logs": self.logs_workspace,
        }

        self._show_workspace("devices")

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
                enabled = bool(action["enabled"])

                if action.get("requires_device", False):
                    enabled = enabled and self.selected_device_id is not None

                button.setEnabled(enabled)
                description = action.get("description") or ""
                capability_id = action.get("capability_id") or ""
                tooltip = (
                    f"{description} [{capability_id}]"
                    if description and capability_id
                    else description or capability_id
                )
                button.setToolTip(tooltip)

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

    def _populate_device_selector(self):
        selected_device_id = self.selected_device_id

        self.device_selector.clear()
        if self.device_registry is None:
            return

        device_ids = list(self.device_registry.snapshot())

        for device_id in device_ids:
            self.device_selector.addItem(str(device_id), device_id)

        if selected_device_id in device_ids:
            index = self.device_selector.findData(selected_device_id)
            if index >= 0:
                self.device_selector.setCurrentIndex(index)
        elif selected_device_id is None:
            self.device_selector.setCurrentIndex(-1)
            self.device_selector.setPlaceholderText("Select a device")
        elif device_ids:
            self.device_selector.setCurrentIndex(0)

    def _on_device_selected(self, index):
        if index < 0:
            self.selected_device_id = None
        else:
            self.selected_device_id = self.device_selector.itemData(index)

        self._update_device_details()

        if hasattr(self, "operation_result_device"):
            self.operation_result_device.setText(
                f"Device: {self.selected_device_id or '-'}"
            )

        if not hasattr(self, "module_action_buttons"):
            return

        for module_id, buttons in self.module_action_buttons.items():
            module = self.module_adapter.registry.get(module_id)
            if module is None:
                continue

            actions = {
                action.id: action
                for action in module.get_actions()
            }

            for action_id, button in buttons.items():
                action = actions.get(action_id)
                if action is None:
                    continue

                enabled = bool(action.enabled)

                if action.requires_device:
                    enabled = (
                        enabled
                        and self.selected_device_id is not None
                    )

                if enabled and action.capability_id:
                    device = None
                    if self.selected_device_id is not None and self.device_registry is not None:
                        device = self.device_registry.get(self.selected_device_id)

                    capabilities = getattr(device, 'capabilities', None)
                    if capabilities is not None:
                        enabled = action.capability_id in capabilities

                if enabled and action.allowed_transports is not None:
                    device = None
                    if self.selected_device_id is not None and self.device_registry is not None:
                        device = self.device_registry.get(self.selected_device_id)

                    transport = getattr(device, 'transport', None)
                    enabled = transport in action.allowed_transports

                if enabled and action.allowed_states is not None:
                    device = None
                    if self.selected_device_id is not None and self.device_registry is not None:
                        device = self.device_registry.get(self.selected_device_id)

                    state = getattr(device, 'state', None)
                    state_value = getattr(state, 'value', state)
                    enabled = state_value in action.allowed_states

                button.setEnabled(enabled)

    def _update_device_details(self):
        if self.device_registry is None or self.selected_device_id is None:
            self.device_details.setText("No device selected.")
            self.device_model.setText("Model: Unknown")
            self.device_serial.setText("Serial: Unknown")
            self.device_state.setText("State: Unknown")
            self.device_transport.setText("Transport: Unknown")
            self.device_module_type.setText("Module: Unknown")
            self.device_brand.setText("Brand: Unknown")
            self.device_android_version.setText("Android: Unknown")
            return

        device = self.device_registry.get(self.selected_device_id)
        if device is None:
            self.device_details.setText("No device selected.")
            self.device_model.setText("Model: Unknown")
            self.device_serial.setText("Serial: Unknown")
            self.device_state.setText("State: Unknown")
            self.device_transport.setText("Transport: Unknown")
            self.device_module_type.setText("Module: Unknown")
            self.device_brand.setText("Brand: Unknown")
            self.device_android_version.setText("Android: Unknown")
            return

        model = getattr(device, "model", None) or "Unknown"
        serial = getattr(device, "serial", None) or "Unknown"
        state = getattr(device, "state", None) or "Unknown"
        transport = getattr(device, "transport", None) or "Unknown"
        module_type = getattr(device, "module_type", None) or "Unknown"
        self.device_details.setText(
        f"Device: {device.device_id} | "
        f"Model: {model} | "
        f"Serial: {serial} | "
        f"State: {state} | "
        f"Transport: {transport} | "
        f"Module: {module_type}"
    )
        self.device_model.setText(f"Model: {model}")
        self.device_serial.setText(f"Serial: {serial}")
        self.device_state.setText(f"State: {state}")
        self.device_transport.setText(f"Transport: {transport}")
        self.device_module_type.setText(f"Module: {module_type}")
        properties = getattr(device, "properties", {}) or {}
        brand = properties.get("brand") or "Unknown"
        android_version = properties.get("android_version") or "Unknown"
        self.device_brand.setText(f"Brand: {brand}")
        self.device_android_version.setText(f"Android: {android_version}")

    def refresh_device_selector(self):
        self._populate_device_selector()
        self._update_device_details()

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

            device = None
            if getattr(action, "requires_device", False):
                if self.device_registry is None:
                    raise ValueError("No device registry is configured.")

                if not self.selected_device_id:
                    raise ValueError("No device is selected.")

                device = self.device_registry.get(self.selected_device_id)
                if device is None:
                    raise ValueError(
                        f"Selected device not found: {self.selected_device_id}"
                    )

            result = self.module_adapter.execute_action(
                module_id,
                action_id,
                device=device,
            )

            result_message = getattr(result, "message", None) or str(result)

            self._update_operation_result(
                module_id,
                action_id,
                result,
            )

            message = result_message

            result_data = getattr(result, "data", None)
            if getattr(result, "success", True) and result_data:
                import json

                message = (
                    f"{message}\n\n"
                    f"Result data:\n{json.dumps(result_data, indent=2, default=str)}"
                )

            if not getattr(result, "success", True):
                error_code = getattr(result, "error_code", None)
                if error_code:
                    message = f"{message}\n\nError code: {error_code}"

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

    def _update_operation_result(self, module_id, action_id, result):
        """Update the persistent GUI surface with the latest operation result."""
        success = getattr(result, "success", True)
        message = getattr(result, "message", None) or str(result)
        result_data = getattr(result, "data", None)
        error_code = getattr(result, "error_code", None)

        self.operation_result_operation.setText(
            f"Operation: {module_id}.{action_id}"
        )
        self.operation_result_status.setText(
            "Status: Success" if success else "Status: Failed"
        )
        self.operation_result_message.setText(
            f"Message: {message}"
        )

        if success and result_data:
            import json

            self.operation_result_details.setPlainText(
                json.dumps(result_data, indent=2, default=str)
            )
        elif not success and error_code:
            self.operation_result_details.setPlainText(
                f"Error code: {error_code}"
            )
        else:
            self.operation_result_details.clear()

    def _show_workspace(self, workspace_id):
        """Show one registered workspace and hide the others."""
        workspace = self._workspaces[workspace_id]

        for candidate in self._workspaces.values():
            candidate.setVisible(candidate is workspace)

        workspace.raise_()

    def open_dashboard(self):
        """Show the main dashboard workspace."""
        self._show_workspace("dashboard")

    def open_devices(self):
        """Show the device operations workspace."""
        self._show_workspace("devices")

    def open_tools(self):
        """Show the available device tools workspace."""
        self._show_workspace("devices")

    def open_database(self):
        """Open the database navigation surface."""
        QMessageBox.information(
            self,
            "Database",
            "Database workspace is not implemented yet.",
        )

    def open_logs(self):
        """Show the logs workspace."""
        self._show_workspace("logs")

    def open_settings(self):
        """Open the settings navigation surface."""
        QMessageBox.information(
            self,
            "Settings",
            "Settings workspace is not implemented yet.",
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
