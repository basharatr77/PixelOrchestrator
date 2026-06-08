import sqlite3
import time
import json
import threading
from collections import defaultdict

class EventBroker:
    def __init__(self, db_path="events.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self.subscribers = defaultdict(list)

        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL,
                event_type TEXT,
                payload TEXT
            )
        """)
        self.conn.commit()

    # ---------------------------
    # PUBLISH EVENT (Redis PUBLISH)
    # ---------------------------
    def publish(self, event_type, payload):
        event = {
            "type": event_type,
            "payload": payload,
            "ts": time.time()
        }

        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO events (ts, event_type, payload) VALUES (?, ?, ?)",
                (event["ts"], event_type, json.dumps(payload))
            )
            self.conn.commit()

        # push to live subscribers
        for callback in self.subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                print("Subscriber error:", e)

    # ---------------------------
    # SUBSCRIBE (Redis SUBSCRIBE)
    # ---------------------------
    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    # ---------------------------
    # REPLAY EVENTS (Redis STREAM-like)
    # ---------------------------
    def replay(self, from_id=0):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, ts, event_type, payload FROM events WHERE id > ? ORDER BY id ASC",
            (from_id,)
        )

        for row in cur.fetchall():
            yield {
                "id": row[0],
                "ts": row[1],
                "type": row[2],
                "payload": json.loads(row[3])
            }

    # ---------------------------
    # STREAM WORKER (WebSocket-style loop)
    # ---------------------------
    def stream(self, event_type, handler, poll_interval=1):
        last_id = 0

        while True:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT id, ts, payload FROM events WHERE event_type=? AND id>? ORDER BY id ASC",
                (event_type, last_id)
            )

            rows = cur.fetchall()

            for r in rows:
                last_id = r[0]
                handler({
                    "id": r[0],
                    "ts": r[1],
                    "type": event_type,
                    "payload": json.loads(r[2])
                })

            time.sleep(poll_interval)
