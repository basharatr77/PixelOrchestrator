import asyncio

import pytest

import app.main as app_main


def test_main_cancels_runtime_when_dashboard_fails(monkeypatch):
    runtime_started = asyncio.Event()
    runtime_cancelled = asyncio.Event()

    class FakeRuntime:
        def __init__(self):
            self.bus = object()

        async def run(self):
            runtime_started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                runtime_cancelled.set()
                raise

    async def failing_dashboard(bus):
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
