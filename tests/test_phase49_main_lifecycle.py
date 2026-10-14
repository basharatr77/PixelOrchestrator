import asyncio

import pytest

import app.main as app_main


def test_main_cancels_runtime_when_dashboard_fails(monkeypatch):
    runtime_started = asyncio.Event()
    runtime_cancelled = asyncio.Event()

    class FakeRuntime:
        def __init__(self, database=None):
            self.bus = object()

        async def run(self):
            runtime_started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                runtime_cancelled.set()
                raise

    async def failing_dashboard(bus, host="0.0.0.0", port=8765, **kwargs):
        raise RuntimeError("dashboard startup failed")

    async def scenario():
        monkeypatch.setattr(app_main, "BusRuntime", FakeRuntime)
        monkeypatch.setattr(app_main, "run_dashboard", failing_dashboard)

        main_task = asyncio.create_task(app_main.main())

        await runtime_started.wait()

        with pytest.raises(RuntimeError, match="dashboard startup failed"):
            await main_task

        assert runtime_cancelled.is_set()

    asyncio.run(scenario())

def test_main_cancels_dashboard_when_runtime_fails(monkeypatch):
    dashboard_started = asyncio.Event()
    dashboard_cancelled = asyncio.Event()

    class FakeRuntime:
        def __init__(self, database=None):
            self.bus = object()

        async def run(self):
            await dashboard_started.wait()
            raise RuntimeError("runtime execution failed")

    async def waiting_dashboard(bus, host="0.0.0.0", port=8765, **kwargs):
        dashboard_started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            dashboard_cancelled.set()
            raise

    async def scenario():
        monkeypatch.setattr(app_main, "BusRuntime", FakeRuntime)
        monkeypatch.setattr(app_main, "run_dashboard", waiting_dashboard)

        with pytest.raises(RuntimeError, match="runtime execution failed"):
            await app_main.main()

        assert dashboard_cancelled.is_set()

    asyncio.run(scenario())
