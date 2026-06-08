import sqlite3
import threading

DB = "consumer_offsets.db"


class ConsumerStore:
    """
    Stores per-consumer-group offsets (Kafka concept)
    """

    def __init__(self):
        self.conn = sqlite3.connect(DB, check_same_thread=False)
        self.lock = threading.Lock()
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS offsets (
            group_id TEXT,
            event_type TEXT,
            offset INTEGER,
            PRIMARY KEY (group_id, event_type)
        )
        """)
        self.conn.commit()

    def get_offset(self, group_id, event_type):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT offset FROM offsets
            WHERE group_id=? AND event_type=?
        """, (group_id, event_type))

        row = cur.fetchone()
        return row[0] if row else 0

    def commit(self, group_id, event_type, offset):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO offsets
                (group_id, event_type, offset)
                VALUES (?, ?, ?)
            """, (group_id, event_type, offset))
            self.conn.commit()
