import sqlite3
import json
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

    def get_events(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events")
        return cursor.fetchall()
