import json
import sqlite3
import json

DB = "event_store.db"


class EventStore:
    def __init__(self):
        self.conn = sqlite3.connect(DB, check_same_thread=False)
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            type TEXT,
            ts REAL,
            payload TEXT
        )
        """)
        self.conn.commit()

    def save(self, event):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?)",
            (
                event.id,
                event.type,
                event.ts,
                json.dumps(event.payload)
            )
        )
        self.conn.commit()
