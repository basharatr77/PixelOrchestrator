import sqlite3

DB = "devices.db"


def create_registry_table(db=None):
    database = DB if db is None else db
    conn = sqlite3.connect(database)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device TEXT UNIQUE,
        status TEXT,
        last_offset INTEGER NOT NULL DEFAULT 0
    )
    """)

    # Upgrade existing databases safely.
    columns = {
        row[1]
        for row in c.execute("PRAGMA table_info(registry)")
    }

    if "last_offset" not in columns:
        c.execute(
            "ALTER TABLE registry ADD COLUMN last_offset "
            "INTEGER NOT NULL DEFAULT 0"
        )

    conn.commit()
    conn.close()


def update_registry(device, status, offset=0, db=None):
    database = DB if db is None else db
    conn = sqlite3.connect(database)
    c = conn.cursor()

    row = c.execute(
        "SELECT last_offset FROM registry WHERE device=? "
        "ORDER BY id DESC LIMIT 1",
        (device,),
    ).fetchone()

    # Ignore stale and duplicate events.
    if row is not None and offset <= row[0]:
        conn.close()
        return False

    # Keep exactly one current registry row.
    c.execute(
        "DELETE FROM registry WHERE device=?",
        (device,),
    )

    c.execute(
        "INSERT INTO registry (device, status, last_offset) "
        "VALUES (?, ?, ?)",
        (device, status, offset),
    )

    conn.commit()
    conn.close()

    return True


def read_registry(db=None):
    database = DB if db is None else db
    conn = sqlite3.connect(database)
    try:
        rows = conn.execute(
            """
            SELECT device, status, last_offset
            FROM registry
            ORDER BY id
            """
        ).fetchall()
    finally:
        conn.close()

    return rows
