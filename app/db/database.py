import sqlite3

DB_NAME = "devices.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_device(name, status="connected"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO devices (name, status) VALUES (?, ?)",
        (name, status)
    )

    conn.commit()
    conn.close()

def create_events_table():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        payload TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def add_event(event_type, payload):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO events (event_type,payload) VALUES (?,?)",
        (event_type, str(payload))
    )

    conn.commit()
    conn.close()

def create_registry_table():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS device_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_name TEXT UNIQUE,
        status TEXT,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def update_registry(device_name, status):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO device_registry(device_name,status)
    VALUES(?,?)
    ON CONFLICT(device_name)
    DO UPDATE SET
        status=excluded.status,
        last_seen=CURRENT_TIMESTAMP
    """, (device_name, status))

    conn.commit()
    conn.close()
