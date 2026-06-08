import sqlite3

DB = "devices.db"

def create_registry_table():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

def update_registry(device, status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM registry WHERE device=?", (device,))
    c.execute("INSERT INTO registry (device, status) VALUES (?, ?)", (device, status))

    conn.commit()
    conn.close()
