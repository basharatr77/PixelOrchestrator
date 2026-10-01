import json

import pytest

from app.config import load_config


@pytest.mark.parametrize("host", ["", "   ", None])
def test_load_config_rejects_invalid_host_value(
    tmp_path, monkeypatch, host
):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "host": host,
                "port": 8000,
                "database": "devices.db",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="host"):
        load_config()
