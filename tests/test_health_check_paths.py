from pathlib import Path

import app.health_check as health_check


def test_health_check_uses_project_root_relative_database_paths():
    project_root = Path(health_check.__file__).resolve().parents[1]

    assert health_check.REGISTRY_DB == project_root / "devices.db"
    assert health_check.EVENT_LOG_DB == project_root / "event_stream.db"
