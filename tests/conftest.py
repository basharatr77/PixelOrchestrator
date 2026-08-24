import pytest


@pytest.fixture(autouse=True)
def isolate_event_bus_databases(tmp_path, monkeypatch):
    event_db = tmp_path / "event_stream.db"
    offsets_db = tmp_path / "consumer_offsets.db"

    monkeypatch.setattr(
        "app.core.event_log.DB",
        str(event_db),
    )

    monkeypatch.setattr(
        "app.core.consumer_store.DB",
        str(offsets_db),
    )
