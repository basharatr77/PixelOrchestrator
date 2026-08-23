import sqlite3

from app.core import registry


def test_registry_creates_and_updates_device(tmp_path, monkeypatch):
    db_path = tmp_path / "devices.db"

    monkeypatch.setattr(registry, "DB", str(db_path))

    registry.create_registry_table()
    registry.update_registry("PIXEL_8", "ADB")

    conn = sqlite3.connect(db_path)

    row = conn.execute(
        "SELECT device, status FROM registry"
    ).fetchone()

    conn.close()

    assert row == ("PIXEL_8", "ADB")
