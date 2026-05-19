"""
Event Bus – Central communication hub
"""

from enum import Enum
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading
import queue

class EventType(Enum):
    """Types of events in the system."""
    DEVICE_DETECTED = "device_detected"
    DEVICE_STATE_CHANGE = "device_state_change"
    DEVICE_DISCONNECTED = "device_disconnected"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_TIMEOUT = "job_timeout"
    JOB_CANCELLED = "job_cancelled"
    WORKER_STARTED = "worker_started"
    WORKER_STOPPED = "worker_stopped"
    OPERATION_START = "operation_start"
    OPERATION_END = "operation_end"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class Event:
    """Event structure."""
    type: EventType
    data: Dict[str, Any]
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

class EventBus:
    """Central event bus for decoupled communication."""
    
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
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._all_subscribers: List[Callable] = []
        self._lock = threading.Lock()
        self._event_queue = queue.Queue()
        self._processing = True
        self._processor_thread = threading.Thread(target=self._process_events, daemon=True)
        self._processor_thread.start()
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to a specific event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable):
        """Subscribe to all events."""
        with self._lock:
            self._all_subscribers.append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from event."""
        with self._lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def emit(self, event: Event):
        """Emit an event (non-blocking)."""
        self._event_queue.put(event)
    
    def emit_sync(self, event: Event):
        """Emit event synchronously (blocking)."""
        self._process_event(event)
    
    def _process_events(self):
        """Background event processor."""
        while self._processing:
            try:
                event = self._event_queue.get(timeout=0.1)
                self._process_event(event)
            except queue.Empty:
                continue
    
    def _process_event(self, event: Event):
        """Process a single event."""
        # Notify all subscribers
        with self._lock:
            # Specific subscribers
            if event.type in self._subscribers:
                for callback in self._subscribers[event.type]:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"Event callback error: {e}")
            
            # Global subscribers
            for callback in self._all_subscribers:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Global callback error: {e}")
    
    def stop(self):
        """Stop event processor."""
        self._processing = False

# Global event bus instance
event_bus = EventBus()