import asyncio
import json

from app.core.broadcaster import Broadcaster
from app.core.event_bus import StreamBus
from app.dashboard import ws_server


class FakeWebSocket:
    def __init__(self, messages=None):
        self.messages = list(messages or [])
        self.sent = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            return self.messages.pop(0)
        raise StopAsyncIteration

    async def send(self, message):
        self.sent.append(message)


def test_dashboard_connection_requires_valid_token(monkeypatch):
    monkeypatch.setattr(
        ws_server,
        "replay_dashboard",
        _unexpected_replay,
    )

    async def scenario():
        broadcaster = Broadcaster()
        monkeypatch.setattr(ws_server, "broadcaster", broadcaster)

        ws = FakeWebSocket([
            json.dumps({
                "type": "dashboard_connect",
                "last_offset": 0,
                "token": "wrong-token",
            })
        ])

        handler = ws_server.create_handler(
            StreamBus(),
            dashboard_token="expected-token",
        )
        await handler(ws)

        assert not broadcaster.dashboard_clients
        assert not any(
            json.loads(message).get("type") == "dashboard_connected"
            for message in ws.sent
        )

    asyncio.run(scenario())


def test_authenticated_dashboard_can_replay_events(monkeypatch):
    replayed = []

    async def fake_replay(ws, offset):
        replayed.append((ws, offset))

    monkeypatch.setattr(ws_server, "replay_dashboard", fake_replay)

    async def scenario():
        broadcaster = Broadcaster()
        monkeypatch.setattr(ws_server, "broadcaster", broadcaster)

        ws = FakeWebSocket([
            json.dumps({
                "type": "dashboard_connect",
                "last_offset": 25,
                "token": "expected-token",
            })
        ])

        handler = ws_server.create_handler(
            StreamBus(),
            dashboard_token="expected-token",
        )
        await handler(ws)

        assert replayed == [(ws, 25)]
        assert not broadcaster.dashboard_clients

    asyncio.run(scenario())


def test_live_dashboard_broadcast_excludes_agent_connections():
    async def scenario():
        broadcaster = Broadcaster()
        dashboard = FakeWebSocket()
        agent = FakeWebSocket()

        await broadcaster.register(agent)
        await broadcaster.register_dashboard(dashboard)

        await broadcaster.broadcast_dashboard({
            "type": "TASK_EXECUTED",
            "payload": {"task_id": "task-1"},
        })

        assert len(dashboard.sent) == 1
        assert agent.sent == []

        await broadcaster.unregister_dashboard(dashboard)
        await broadcaster.unregister(agent)

    asyncio.run(scenario())


async def _unexpected_replay(ws, offset):
    raise AssertionError("Unauthenticated dashboard must not replay events.")
