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
    cur.execute("INSERT INTO devices (name, status) VALUES (?, ?)", (name, status))
    conn.commit()
    conn.close()
