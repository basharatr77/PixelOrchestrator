import json

import pytest

from app.config import load_config


@pytest.mark.parametrize("payload", [[], None, "invalid"])
def test_load_config_rejects_non_object_json(
    tmp_path, monkeypatch, payload
):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    monkeypatch.setattr("app.config.CONFIG_FILE", config_file)

    with pytest.raises(ValueError, match="configuration object"):
        load_config()
