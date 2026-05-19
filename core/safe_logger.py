"""
Thread-safe logging for GUI
"""

from PySide6.QtCore import QObject, Signal
import threading
import queue

class SafeLogger(QObject):
    """Thread-safe logger for GUI updates."""
    
    log_signal = Signal(str)
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        super().__init__()
        self._queue = queue.Queue()
        self._processing = True
        self._thread = threading.Thread(target=self._process, daemon=True)
        self._thread.start()
    
    def log(self, message: str):
        """Thread-safe log from any thread."""
        self._queue.put(message)
    
    def _process(self):
        """Process log messages in main thread style."""
        while self._processing:
            try:
                msg = self._queue.get(timeout=0.1)
                self.log_signal.emit(msg)
            except queue.Empty:
                continue
    
    def stop(self):
        self._processing = False

safe_logger = SafeLogger()