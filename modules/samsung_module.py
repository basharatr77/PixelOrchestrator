from core.base_module import BaseModule
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QPlainTextEdit, QSplitter
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

class SamsungModule(BaseModule):
    @property
    def name(self): return "Samsung"
    @property
    def icon(self): return "⭐"

    def create_ui(self, parent=None):
        self.launcher = parent
        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 10))
        self.terminal.setStyleSheet("background-color: #121212; color: #00ff00;")
        layout.addWidget(self.terminal)
        btn = QPushButton("Placeholder - Samsung Tools")
        btn.clicked.connect(lambda: self.log_message("Samsung module - to be implemented"))
        layout.addWidget(btn)
        return self.main_widget

    @Slot(str)
    def log_message(self, text): self.terminal.appendPlainText(text)
