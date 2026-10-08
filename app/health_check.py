from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DB = PROJECT_ROOT / "devices.db"
EVENT_LOG_DB = PROJECT_ROOT / "event_stream.db"


def run_health_check(database=None):
    registry_db = REGISTRY_DB if database is None else Path(database)

    registry_exists = Path(registry_db).exists()
    event_log_exists = Path(EVENT_LOG_DB).exists()

    devices = []
    event_count = 0
    registry_error = None
    event_log_error = None

    if registry_exists:
        try:
            conn = sqlite3.connect(registry_db)
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
        except sqlite3.Error as exc:
            registry_error = type(exc).__name__

    if event_log_exists:
        try:
            conn = sqlite3.connect(EVENT_LOG_DB)
            try:
                event_count = conn.execute(
                    "SELECT COUNT(*) FROM event_log"
                ).fetchone()[0]
            finally:
                conn.close()
        except sqlite3.Error as exc:
            event_log_error = type(exc).__name__

    return {
        "registry_exists": registry_exists,
        "registry_error": registry_error,
        "event_log_exists": event_log_exists,
        "event_log_error": event_log_error,
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
