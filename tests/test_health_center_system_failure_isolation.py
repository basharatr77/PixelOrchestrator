from pathlib import Path
import sqlite3

from app import health_check


def test_health_check_reports_sqlite_failures_without_aborting(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda _path: True)

    def fail_connect(_path):
        raise sqlite3.DatabaseError("database is malformed")

    monkeypatch.setattr(health_check.sqlite3, "connect", fail_connect)

    result = health_check.run_health_check(database="broken-registry.db")

    assert result["registry_exists"] is True
    assert result["event_log_exists"] is True
    assert result["registry_error"] == "DatabaseError"
    assert result["event_log_error"] == "DatabaseError"
    assert result["devices"] == []
    assert result["event_count"] == 0
