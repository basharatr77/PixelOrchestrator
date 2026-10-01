import json

import pytest

from app.config import load_config


@pytest.mark.parametrize("port", [0, -1, 65536, 99999])
def test_load_config_rejects_invalid_port_range(
    tmp_path, monkeypatch, port
):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "host": "0.0.0.0",
                "port": port,
                "database": "devices.db",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="port"):
        load_config()
