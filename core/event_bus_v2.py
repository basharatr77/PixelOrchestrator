"""
Event Bus V2 – Central communication hub for decoupled architecture
"""

from enum import Enum
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading
import queue
import json


class EventType(Enum):
    """Types of events in the system."""
    DEVICE_DETECTED = "device_detected"
    DEVICE_STATE_CHANGE = "device_state_change"
    DEVICE_DISCONNECTED = "device_disconnected"
    JOB_START = "job_start"
    JOB_END = "job_end"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"
    JOB_TIMEOUT = "job_timeout"
    JOB_RETRY = "job_retry"
    JOB_RETRYING = "job_retrying"
    WORKER_STARTED = "worker_started"
    WORKER_STOPPED = "worker_stopped"
    WORKER_BUSY = "worker_busy"
    WORKER_IDLE = "worker_idle"
    OPERATION_START = "operation_start"
    OPERATION_END = "operation_end"
    OPERATION_PROGRESS = "operation_progress"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class Event:
    """Event structure for communication."""
    type: EventType
    data: Dict[str, Any]
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary for serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Event":
        """Create event from dictionary."""
        return cls(
            type=EventType(data["type"]),
            data=data["data"],
            source=data.get("source", ""),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class EventBus:
    """
    Central event bus for decoupled communication between components.
    Supports async event processing, subscriptions, and event persistence.
    """
    
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
        self._event_queue = queue.Queue()
        self._processing = True
        self._persist_events = False
        self._event_history: List[Event] = []
        self._max_history = 1000
        
        # Start processor thread
        self._processor_thread = threading.Thread(target=self._process_events, daemon=True)
        self._processor_thread.start()
        
        print("[EventBus] Initialized")
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to a specific event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable):
        """Subscribe to all events."""
        with self._lock:
            if callback not in self._all_subscribers:
                self._all_subscribers.append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from a specific event type."""
        with self._lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def emit(self, event: Event):
        """Emit an event asynchronously (non-blocking)."""
        self._event_queue.put(event)
        
        # Store history if enabled
        if self._persist_events:
            with self._lock:
                self._event_history.append(event)
                if len(self._event_history) > self._max_history:
                    self._event_history = self._event_history[-self._max_history:]
    
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
            except Exception as e:
                print(f"[EventBus] Processor error: {e}")
    
    def _process_event(self, event: Event):
        """Process a single event and notify subscribers."""
        # Notify specific subscribers
        with self._lock:
            if event.type in self._subscribers:
                for callback in self._subscribers[event.type]:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"[EventBus] Callback error for {event.type}: {e}")
            
            # Notify all subscribers
            for callback in self._all_subscribers:
                try:
                    callback(event)
                except Exception as e:
                    print(f"[EventBus] Global callback error: {e}")
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """Get event history, optionally filtered by type."""
        with self._lock:
            if event_type:
                return [e for e in self._event_history[-limit:] if e.type == event_type]
            return self._event_history[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
    
    def enable_persistence(self, enabled: bool):
        """Enable or disable event persistence."""
        self._persist_events = enabled
    
    def stop(self):
        """Stop the event bus processor."""
        self._processing = False
        print("[EventBus] Stopped")


# Global event bus instance
event_bus = EventBus()