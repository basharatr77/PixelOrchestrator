import asyncio

import app.main as app_main


def test_main_passes_runtime_to_dashboard(monkeypatch):
    captured = {}

    class FakeRuntime:
        def __init__(self, database=None):
            self.bus = object()

        async def run(self):
            return None

    async def fake_dashboard(bus, host="0.0.0.0", port=8765, **kwargs):
        captured["bus"] = bus

    monkeypatch.setattr(app_main, "BusRuntime", FakeRuntime)
    monkeypatch.setattr(app_main, "run_dashboard", fake_dashboard)

    asyncio.run(app_main.main())

    assert captured["bus"] is not None
