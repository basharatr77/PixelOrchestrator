import time, json, sqlite3, threading, queue
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Callable, Dict, Optional
class EventType(Enum):
    JOB_START="job_start"; JOB_END="job_end"; STEP="step"; DEVICE_STATE="device_state"; ERROR="error"
@dataclass
class Event:
    job_id: str; type: EventType; message: str; timestamp: float = field(default_factory=time.time); data: Dict = field(default_factory=dict)
class EventBus:
    def __init__(self, persist=True, db_path="event_bus.db"):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._lock = threading.Lock()
        self._queue = queue.Queue()
        self._persist = persist
        if persist:
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, type TEXT, payload TEXT, timestamp REAL)")
            self._conn.commit()
        self._worker = threading.Thread(target=self._process_queue, daemon=True)
        self._worker.start()
    def subscribe(self, event_type: EventType, callback: Callable):
        with self._lock:
            if event_type not in self._subscribers: self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    def emit(self, event: Event):
        self._queue.put(event)
    def _process_queue(self):
        while True:
            event = self._queue.get()
            with self._lock:
                for cb in self._subscribers.get(event.type, []):
                    try: cb(event)
                    except: pass
            if self._persist:
                try:
                    self._conn.execute("INSERT INTO events (type, payload, timestamp) VALUES (?, ?, ?)",
                                       (event.type.value, json.dumps({"job_id":event.job_id,"message":event.message,"data":event.data}), event.timestamp))
                    self._conn.commit()
                except: pass
