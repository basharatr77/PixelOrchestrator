import asyncio
import json

from app.core.event_bus import StreamBus
from app.dashboard import ws_server


class FakeWebSocket:
    def __init__(self, messages):
        self.messages = iter(messages)
        self.sent = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.messages)
        except StopIteration:
            raise StopAsyncIteration

    async def send(self, message):
        self.sent.append(message)


def test_remote_agent_registration_requires_agent_id():
    async def run():
        bus = StreamBus()

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
            }),
        ])

        handler = ws_server.create_handler(bus)
        await handler(ws)

        assert len(ws.sent) == 1

        response = json.loads(ws.sent[0])

        assert response == {
            "type": "agent_register_response",
            "success": False,
            "error": "agent_id is required",
        }

    asyncio.run(run())


def test_remote_agent_registration_accepts_stable_agent_id():
    async def run():
        bus = StreamBus()

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent-test-001",
            }),
        ])

        handler = ws_server.create_handler(bus)
        await handler(ws)

        assert len(ws.sent) == 1

        response = json.loads(ws.sent[0])

        assert response == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": "agent-test-001",
        }

    asyncio.run(run())


def test_remote_agent_registration_rejects_empty_agent_id():
    async def run():
        bus = StreamBus()

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "",
            }),
        ])

        handler = ws_server.create_handler(bus)
        await handler(ws)

        assert len(ws.sent) == 1

        response = json.loads(ws.sent[0])

        assert response == {
            "type": "agent_register_response",
            "success": False,
            "error": "agent_id is required",
        }

    asyncio.run(run())


def test_remote_agent_registration_rejects_whitespace_agent_id():
    async def run():
        bus = StreamBus()

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "   ",
            }),
        ])

        handler = ws_server.create_handler(bus)
        await handler(ws)

        assert len(ws.sent) == 1

        response = json.loads(ws.sent[0])

        assert response == {
            "type": "agent_register_response",
            "success": False,
            "error": "agent_id is required",
        }

    asyncio.run(run())


def test_remote_agent_registration_rejects_non_string_agent_id():
    async def run():
        for invalid_agent_id in [123, True, [], {}]:
            bus = StreamBus()

            ws = FakeWebSocket([
                json.dumps({
                    "type": "agent_register",
                    "agent_id": invalid_agent_id,
                }),
            ])

            handler = ws_server.create_handler(bus)
            await handler(ws)

            assert len(ws.sent) == 1

            response = json.loads(ws.sent[0])

            assert response == {
                "type": "agent_register_response",
                "success": False,
                "error": "agent_id is required",
            }

    asyncio.run(run())


def test_remote_agent_registration_rejects_second_registration_on_same_connection():
    async def run():
        bus = StreamBus()

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent-test-001",
            }),
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent-test-002",
            }),
        ])

        handler = ws_server.create_handler(bus)
        await handler(ws)

        assert len(ws.sent) == 2

        first_response = json.loads(ws.sent[0])
        second_response = json.loads(ws.sent[1])

        assert first_response == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": "agent-test-001",
        }

        assert second_response == {
            "type": "agent_register_response",
            "success": False,
            "error": "agent already registered",
        }

    asyncio.run(run())


def test_remote_agent_registration_connection_cleanup():
    async def run():
        bus = StreamBus()

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent-test-cleanup",
            }),
        ])

        registered = []
        unregistered = []

        async def fake_register(socket):
            registered.append(socket)

        async def fake_unregister(socket):
            unregistered.append(socket)

        original_register = ws_server.broadcaster.register
        original_unregister = ws_server.broadcaster.unregister

        ws_server.broadcaster.register = fake_register
        ws_server.broadcaster.unregister = fake_unregister

        try:
            handler = ws_server.create_handler(bus)
            await handler(ws)
        finally:
            ws_server.broadcaster.register = original_register
            ws_server.broadcaster.unregister = original_unregister

        assert registered == [ws]
        assert unregistered == [ws]

        assert json.loads(ws.sent[0]) == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": "agent-test-cleanup",
        }

    asyncio.run(run())


def test_remote_agent_registration_allows_same_id_on_new_connection():
    async def run():
        bus = StreamBus()

        ws1 = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent-test-001",
            }),
        ])

        ws2 = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent-test-001",
            }),
        ])

        handler = ws_server.create_handler(bus)

        await handler(ws1)
        await handler(ws2)

        assert json.loads(ws1.sent[0]) == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": "agent-test-001",
        }

        assert json.loads(ws2.sent[0]) == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": "agent-test-001",
        }

    asyncio.run(run())

def test_remote_agent_transport_request_requires_registration():
    async def run():
        bus = StreamBus()

        ws = FakeWebSocket([
            json.dumps({
                "type": "transport_request",
                "request_id": "req-unregistered",
                "operation": "get_device_info",
                "serial": "REMOTE-UNREGISTERED",
                "mode": "ADB",
            }),
        ])

        handler = ws_server.create_handler(bus)
        await handler(ws)

        assert len(ws.sent) == 1

        response = json.loads(ws.sent[0])

        assert response == {
            "type": "transport_response",
            "request_id": "req-unregistered",
            "success": False,
            "error": "agent registration required",
        }

    asyncio.run(run())
