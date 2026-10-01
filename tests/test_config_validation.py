import json

import pytest

from app.config import load_config


def test_load_config_rejects_missing_required_key(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "host": "0.0.0.0",
                "port": 8000,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="database"):
        load_config()
