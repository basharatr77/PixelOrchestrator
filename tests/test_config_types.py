import json

import pytest

from app.config import load_config


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("host", 123, "host"),
        ("port", "8000", "port"),
        ("database", 123, "database"),
    ],
)
def test_load_config_rejects_invalid_value_types(
    tmp_path, monkeypatch, key, value, message
):
    config = {
        "host": "0.0.0.0",
        "port": 8000,
        "database": "devices.db",
    }
    config[key] = value

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match=message):
        load_config()
