import asyncio
import sqlite3
import pytest
from app import main
from app.core.bus_runtime import BusRuntime


def test_main_uses_configured_dashboard_host_and_port(monkeypatch):
    captured = {}

    class FakeRuntime:
        def __init__(self, database=None):
            captured["database"] = database
            self.bus = object()

        async def run(self):
            await asyncio.Future()

    async def fake_dashboard(bus, host="0.0.0.0", port=8765):
        captured["host"] = host
        captured["port"] = port
        raise RuntimeError("stop")

    monkeypatch.setattr(main, "BusRuntime", FakeRuntime)
    monkeypatch.setattr(main, "run_dashboard", fake_dashboard)
    monkeypatch.setattr(
        main,
        "load_config",
        lambda: {"host": "127.0.0.1", "port": 9001, "database": "devices.db"},
        raising=False,
    )

    with pytest.raises(RuntimeError, match="stop"):
        asyncio.run(main.main())

    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 9001





def test_bus_runtime_uses_configured_database_path(tmp_path):
    database = tmp_path / "configured.db"

    runtime = BusRuntime(database=str(database))

    assert database.exists()

    rows = sqlite3.connect(database).execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='registry'"
    ).fetchall()

    assert rows == [("registry",)]
    assert runtime.device_registry is not None

def test_main_uses_configured_database(monkeypatch):
    captured = {}

    class FakeRuntime:
        def __init__(self, database=None):
            captured["database"] = database
            self.bus = object()

        async def run(self):
            await asyncio.Future()

    async def fake_dashboard(bus, host="0.0.0.0", port=8765):
        raise RuntimeError("stop")

    monkeypatch.setattr(main, "BusRuntime", FakeRuntime)
    monkeypatch.setattr(main, "run_dashboard", fake_dashboard)
    monkeypatch.setattr(
        main,
        "load_config",
        lambda: {
            "host": "127.0.0.1",
            "port": 9001,
            "database": "configured.db",
        },
        raising=False,
    )

    with pytest.raises(RuntimeError, match="stop"):
        asyncio.run(main.main())

    assert captured["database"] == "configured.db"
