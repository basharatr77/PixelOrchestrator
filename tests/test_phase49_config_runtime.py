import asyncio
import sqlite3
import pytest
from app import main
import app.core.bus_runtime as bus_runtime_module
from app.core.bus_runtime import BusRuntime
from app.core.task_repository import TaskRepository


def test_main_uses_configured_dashboard_host_and_port(monkeypatch):
    captured = {}

    class FakeRuntime:
        def __init__(self, database=None):
            captured["database"] = database
            self.bus = object()

        async def run(self):
            await asyncio.Future()

    async def fake_dashboard(bus, host="0.0.0.0", port=8765, **kwargs):
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

    async def fake_dashboard(bus, host="0.0.0.0", port=8765, **kwargs):
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
def test_configured_database_task_repository(tmp_path, monkeypatch):
    database = tmp_path / "configured-runtime.db"

    runtime = BusRuntime(database=str(database))

    assert isinstance(runtime.task_repository, TaskRepository)
    assert runtime.task_repository.db_path == str(database)
    task_tables = sqlite3.connect(database).execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='tasks'"
    ).fetchall()
    assert task_tables == [("tasks",)]

    explicit_repository = TaskRepository(tmp_path / "explicit-tasks.db")
    injected_runtime = BusRuntime(
        task_repository=explicit_repository,
        database=str(database),
    )
    assert injected_runtime.task_repository is explicit_repository

    monkeypatch.setattr(
        bus_runtime_module,
        "create_registry_table",
        lambda db=None: None,
    )
    monkeypatch.setattr(
        bus_runtime_module,
        "read_registry",
        lambda db=None: [],
    )
    legacy_runtime = BusRuntime()
    assert legacy_runtime.task_repository is None
