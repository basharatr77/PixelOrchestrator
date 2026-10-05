import asyncio

import app.dashboard.ws_server as ws_server


def test_run_dashboard_uses_supplied_host_and_port(monkeypatch):
    captured = {}

    def fake_serve(handler, host, port):
        captured["handler"] = handler
        captured["host"] = host
        captured["port"] = port

        class FakeServer:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        return FakeServer()

    async def fake_future():
        return None

    monkeypatch.setattr(ws_server, "subscribe_dashboard", lambda bus: None)
    monkeypatch.setattr(
        ws_server,
        "create_handler",
        lambda bus: object(),
    )
    monkeypatch.setattr(ws_server.websockets, "serve", fake_serve)

    class FakeAsyncio:
        @staticmethod
        def Future():
            return fake_future()

    monkeypatch.setattr(ws_server.asyncio, "Future", FakeAsyncio.Future)

    asyncio.run(
        ws_server.run_dashboard(
            object(),
            host="127.0.0.1",
            port=9876,
        )
    )

    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 9876
