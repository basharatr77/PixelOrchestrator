import sqlite3
import json
import threading

DB = "event_stream.db"


class EventLog:
    def __init__(self):
        self.conn = sqlite3.connect(DB, check_same_thread=False)
        self.lock = threading.Lock()
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS event_log (
            offset INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT,
            type TEXT,
            ts REAL,
            payload TEXT
        )
        """)
        self.conn.commit()

    def append(self, event):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO event_log (id, type, ts, payload)
                VALUES (?, ?, ?, ?)
            """, (
                event.id,
                event.type,
                event.ts,
                json.dumps(event.payload)
            ))
            self.conn.commit()

            return cur.lastrowid

    def read_from(self, offset=0, limit=100):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT offset, id, type, ts, payload
            FROM event_log
            WHERE offset > ?
            ORDER BY offset ASC
            LIMIT ?
        """, (offset, limit))

        return [
            {
                "offset": r[0],
                "id": r[1],
                "type": r[2],
                "ts": r[3],
                "payload": json.loads(r[4])
            }
            for r in cur.fetchall()
        ]
