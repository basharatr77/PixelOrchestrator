import sqlite3
import os

DB = "devices.db"

print("\n===== PIXEL ORCHESTRATOR HEALTH CHECK =====\n")

# 1. FILE CHECK
print("[1] File Structure Check")
print("Core exists:", os.path.exists("core"))
print("DB exists:", os.path.exists(DB))

# 2. DEVICE COUNT
print("\n[2] Device Registry")

try:
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM devices")
    print("Devices:", c.fetchone()[0])

    c.execute("SELECT * FROM devices LIMIT 5")
    print("Sample:", c.fetchall())

    conn.close()
except Exception as e:
    print("DB Error:", e)

# 3. EVENT LOG CHECK
print("\n[3] Event Log")

try:
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM event_log")
    print("Events:", c.fetchone()[0])

    conn.close()
except Exception as e:
    print("Event log missing or not initialized:", e)

print("\n===== SYSTEM OK CHECK COMPLETE =====\n")
