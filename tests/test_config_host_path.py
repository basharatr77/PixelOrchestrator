import json

from app.config import load_config


def test_load_config_normalizes_host_whitespace(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "host": " 0.0.0.0 ",
                "port": 8000,
                "database": "devices.db",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    config = load_config()

    assert config["host"] == "0.0.0.0"
