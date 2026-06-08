import sqlite3
import json
<<<<<<< HEAD
from datetime import datetime
=======
<<<<<<< HEAD
>>>>>>> 57b558f (auto update)

class EventStore:

    def __init__(self):
        self.conn = sqlite3.connect("events.db")
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY,
            event_type TEXT,
            payload TEXT,
            timestamp TEXT
        )
        """)
        self.conn.commit()

    def save_event(self, event_type, payload):
        self.conn.execute(
            """
            INSERT INTO events
            (event_type,payload,timestamp)
            VALUES (?,?,?)
            """,
            (
                event_type,
                json.dumps(payload),
                datetime.utcnow().isoformat()
            )
        )
        self.conn.commit()

<<<<<<< HEAD
=======

def save_event(event):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "INSERT INTO event_log (type, payload) VALUES (?, ?)",
        (event.get("type"), json.dumps(event.get("payload")))
    )

    conn.commit()
    conn.close()
=======
from datetime import datetime

class EventStore:

    def __init__(self):
        self.conn = sqlite3.connect("events.db")
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY,
            event_type TEXT,
            payload TEXT,
            timestamp TEXT
        )
        """)
        self.conn.commit()

    def save_event(self, event_type, payload):
        self.conn.execute(
            """
            INSERT INTO events
            (event_type,payload,timestamp)
            VALUES (?,?,?)
            """,
            (
                event_type,
                json.dumps(payload),
                datetime.utcnow().isoformat()
            )
        )
        self.conn.commit()

>>>>>>> 57b558f (auto update)
    def get_events(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events")
        return cursor.fetchall()
<<<<<<< HEAD
=======
>>>>>>> 0900c60 (Stable Event-Driven Core: AI engine, workflow, dedup, replay fix, async event bus hardened)
>>>>>>> 57b558f (auto update)
