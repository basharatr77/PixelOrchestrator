import sqlite3

class ConsumerStore:
    def __init__(self):
        self.db = sqlite3.connect("offsets.db", check_same_thread=False)
        self._init()

    def _init(self):
        cur = self.db.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS offsets (
            group_id TEXT,
            topic TEXT,
            partition INTEGER,
            offset INTEGER,
            PRIMARY KEY (group_id, topic, partition)
        )
        """)
        self.db.commit()

    def get(self, group, topic, partition):
        cur = self.db.cursor()
        cur.execute("""
            SELECT offset FROM offsets
            WHERE group_id=? AND topic=? AND partition=?
        """, (group, topic, partition))

        row = cur.fetchone()
        return row[0] if row else 0

    def commit(self, group, topic, partition, offset):
        cur = self.db.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO offsets VALUES (?, ?, ?, ?)
        """, (group, topic, partition, offset))
        self.db.commit()
