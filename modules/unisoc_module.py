from core.base_module import BaseModule
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QPushButton
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont

class UnisocModule(BaseModule):
    @property
    def name(self): return "Unisoc"
    @property
    def icon(self): return "🌐"

    def create_ui(self, parent=None):
        self.launcher = parent
        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 10))
        self.terminal.setStyleSheet("background-color: #121212; color: #00ff00;")
        layout.addWidget(self.terminal)
        btn = QPushButton("Unisoc Tools (Placeholder)")
        btn.clicked.connect(lambda: self.log_message("Unisoc module - coming soon"))
        layout.addWidget(btn)
        return self.main_widget

    @Slot(str)
    def log_message(self, text): self.terminal.appendPlainText(text)
