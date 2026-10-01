from pathlib import Path

from app.config import load_config


def test_load_config_returns_project_configuration():
    config = load_config()

    assert config["host"] == "0.0.0.0"
    assert config["port"] == 8000
    assert config["database"] == str(
        Path(__file__).resolve().parents[1] / "devices.db"
    )
