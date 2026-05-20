"""
AI Chat Assistant Widget – Live AI Help for Device Flashing
FIXED: Proper expansion on maximize
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread


class AIQueryThread(QThread):
    result_signal = Signal(str)
    error_signal = Signal(str)
    
    def __init__(self, ai_service, question, context=""):
        super().__init__()
        self.ai_service = ai_service
        self.question = question
        self.context = context
    
    def run(self):
        try:
            response = self.ai_service.chat(self.question, self.context)
            self.result_signal.emit(response)
        except Exception as e:
            self.error_signal.emit(str(e))


class AIChatWidget(QWidget):
    def __init__(self, ai_service, parent=None):
        super().__init__(parent)
        self.ai_service = ai_service
        self._current_thread = None
        # Ensure this widget expands to fill available space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header – fixed height
        header = QLabel("🤖 AI Assistant - Ask me anything about device flashing!")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px; background-color: #2d2d2d; border-radius: 5px;")
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setMinimumHeight(40)
        layout.addWidget(header)
        
        # Chat history – takes all remaining space
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("AI responses will appear here...")
        self.chat_history.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-family: Consolas; font-size: 11pt;")
        self.chat_history.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.chat_history, 1)  # stretch factor
        
        # Input area – fixed height
        input_widget = QWidget()
        input_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask anything about device flashing, adb, fastboot, bootloader, recovery...")
        self.input_box.returnPressed.connect(self.send_query)
        self.input_box.setStyleSheet("padding: 10px; font-size: 12px;")
        self.input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.send_btn = QPushButton("📤 Send")
        self.send_btn.clicked.connect(self.send_query)
        self.send_btn.setStyleSheet("background-color: #3a6ea5; padding: 10px 20px; font-weight: bold;")
        self.send_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.send_btn.setMinimumWidth(80)
        
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)
        layout.addWidget(input_widget)
        
        # Status bar – fixed height
        status_widget = QWidget()
        status_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("⚡ AI Assistant Ready")
        self.status_label.setStyleSheet("color: #00ff00;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(120)
        self.progress.setVisible(False)
        status_layout.addWidget(self.progress)
        
        layout.addWidget(status_widget)
        
        # Examples – fixed height
        examples_frame = QWidget()
        examples_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        examples_frame.setStyleSheet("background-color: #2d2d2d; border-radius: 5px; padding: 4px;")
        examples_layout = QHBoxLayout(examples_frame)
        examples_layout.setContentsMargins(4, 4, 4, 4)
        examples = QLabel("💡 Examples: How to flash boot image? | What is fastbootd? | How to fix bootloop? | Backup partitions")
        examples.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        examples_layout.addWidget(examples)
        layout.addWidget(examples_frame)
        
        # Check AI availability
        if not self.ai_service.is_available():
            self.input_box.setEnabled(False)
            self.input_box.setPlaceholderText("❌ AI Assistant not available. Please install Ollama")
            self.send_btn.setEnabled(False)
            self.status_label.setText("⚠️ AI Assistant Not Available")
            self.status_label.setStyleSheet("color: #ff4444;")
            self.chat_history.append("<b style='color:#ff4444'>⚠️ AI Assistant Not Available</b>")
            self.chat_history.append("Please install Ollama from https://ollama.com")
            self.chat_history.append("Then run: <b>ollama pull llama3.2:3b</b>")
        else:
            self.chat_history.append("<b>🤖 AI Assistant:</b> Hello! I'm your AI assistant for device flashing.")
            self.chat_history.append("Ask me anything about ADB, fastboot, bootloader, recovery, partitions, backups, or troubleshooting.")
    
    def send_query(self):
        question = self.input_box.text().strip()
        if not question:
            return
        self.input_box.clear()
        self.chat_history.append(f"<b>👤 You:</b> {question}")
        
        self.input_box.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.status_label.setText("🤔 AI is thinking...")
        self.status_label.setStyleSheet("color: #ffaa00;")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        
        context = self.get_device_context()
        self._current_thread = AIQueryThread(self.ai_service, question, context)
        self._current_thread.result_signal.connect(self.on_result)
        self._current_thread.error_signal.connect(self.on_error)
        self._current_thread.start()
    
    def on_result(self, response):
        self.chat_history.append(f"<b style='color:#00a8ff'>🤖 AI:</b> {response}")
        self.chat_history.append("")
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
        self.status_label.setText("✅ AI Assistant Ready")
        self.status_label.setStyleSheet("color: #00ff00;")
        self.progress.setVisible(False)
        self.input_box.setEnabled(True)
        self.send_btn.setEnabled(True)
        self._current_thread = None
    
    def on_error(self, error):
        self.chat_history.append(f"<b style='color:red'>❌ Error:</b> {error}")
        self.chat_history.append("")
        self.status_label.setText("⚠️ AI Assistant Error")
        self.status_label.setStyleSheet("color: #ff4444;")
        self.progress.setVisible(False)
        self.input_box.setEnabled(True)
        self.send_btn.setEnabled(True)
        self._current_thread = None
    
    def get_device_context(self) -> str:
        try:
            from core.transport import Transport
            from core.adb_manager import AdbManager
            transport = Transport()
            adb = AdbManager(transport)
            devices = adb.devices()
            if devices:
                context = f"Connected device: {devices[0][0]} in mode {devices[0][1]}\n"
                try:
                    result = adb.shell("getprop ro.product.model", serial=devices[0][0])
                    if result.success and result.stdout:
                        context += f"Device model: {result.stdout.strip()}\n"
                    result = adb.shell("getprop ro.build.version.release", serial=devices[0][0])
                    if result.success and result.stdout:
                        context += f"Android version: {result.stdout.strip()}\n"
                except:
                    pass
                return context
        except:
            pass
        return "No device connected"
    
    def clear_history(self):
        self.chat_history.clear()
        self.chat_history.append("<b>🤖 AI Assistant:</b> Chat history cleared. How can I help you?")