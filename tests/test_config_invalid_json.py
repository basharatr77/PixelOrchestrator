import pytest

from app.config import load_config


def test_load_config_rejects_invalid_json(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"host": "0.0.0.0", "port": ',
        encoding="utf-8",
    )

    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="Invalid configuration JSON"):
        load_config()
