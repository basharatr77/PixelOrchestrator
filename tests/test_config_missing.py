import pytest

from app.config import load_config


def test_load_config_rejects_missing_config_file(tmp_path, monkeypatch):
    config_file = tmp_path / "missing-config.json"
    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="Configuration file not found"):
        load_config()
