import sqlite3

from app import health_check


def test_health_check_uses_authoritative_registry_and_event_log(
    tmp_path,
    monkeypatch,
):
    registry_db = tmp_path / "devices.db"
    event_log_db = tmp_path / "event_stream.db"

    conn = sqlite3.connect(registry_db)
    conn.execute(
        """
        CREATE TABLE registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT,
            status TEXT,
            last_offset INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        "INSERT INTO registry (device, status, last_offset) "
        "VALUES (?, ?, ?)",
        ("TEST_DEVICE", "ADB", 7),
    )
    conn.commit()
    conn.close()

    conn = sqlite3.connect(event_log_db)
    conn.execute(
        """
        CREATE TABLE event_log (
            offset INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT,
            type TEXT,
            ts REAL,
            payload TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO event_log (id, type, ts, payload) "
        "VALUES (?, ?, ?, ?)",
        ("event-1", "device.connected", 1.0, "{}"),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(health_check, "REGISTRY_DB", str(registry_db))
    monkeypatch.setattr(health_check, "EVENT_LOG_DB", str(event_log_db))

    result = health_check.run_health_check()

    assert result["device_count"] == 1
    assert result["devices"] == [("TEST_DEVICE", "ADB", 7)]
    assert result["event_count"] == 1
