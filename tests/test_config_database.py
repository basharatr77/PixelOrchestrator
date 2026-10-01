import json

import pytest

from app.config import load_config


@pytest.mark.parametrize("database", ["", "   ", None])
def test_load_config_rejects_invalid_database_value(
    tmp_path, monkeypatch, database
):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "host": "0.0.0.0",
                "port": 8000,
                "database": database,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="database"):
        load_config()
