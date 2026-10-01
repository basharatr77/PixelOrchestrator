import sqlite3
import os

REGISTRY_DB = "devices.db"
EVENT_LOG_DB = "event_stream.db"


def run_health_check():
    registry_exists = os.path.exists(REGISTRY_DB)
    event_log_exists = os.path.exists(EVENT_LOG_DB)

    devices = []
    event_count = 0

    if registry_exists:
        conn = sqlite3.connect(REGISTRY_DB)
        try:
            devices = conn.execute(
                """
                SELECT device, status, last_offset
                FROM registry
                ORDER BY id
                """
            ).fetchall()
        finally:
            conn.close()

    if event_log_exists:
        conn = sqlite3.connect(EVENT_LOG_DB)
        try:
            event_count = conn.execute(
                "SELECT COUNT(*) FROM event_log"
            ).fetchone()[0]
        finally:
            conn.close()

    return {
        "registry_exists": registry_exists,
        "event_log_exists": event_log_exists,
        "device_count": len(devices),
        "devices": devices,
        "event_count": event_count,
    }


def main():
    print("\n===== PIXEL ORCHESTRATOR HEALTH CHECK =====\n")

    result = run_health_check()

    print("[1] Device Registry")
    print("DB exists:", result["registry_exists"])
    print("Devices:", result["device_count"])
    print("Sample:", result["devices"][:5])

    print("\n[2] Event Log")
    print("DB exists:", result["event_log_exists"])
    print("Events:", result["event_count"])

    print("\n===== SYSTEM HEALTH CHECK COMPLETE =====\n")


if __name__ == "__main__":
    main()
