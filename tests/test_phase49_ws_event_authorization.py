import asyncio
import json

from app.dashboard import ws_server


class FakeWebSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            return self.messages.pop(0)
        raise StopAsyncIteration

    async def send(self, message):
        self.sent.append(message)


def test_unauthenticated_socket_cannot_publish_unknown_event(monkeypatch):
    published = []

    class FakeBus:
        async def publish(self, event):
            published.append(event)

    async def fake_register(socket):
        pass

    async def fake_unregister(socket):
        pass

    monkeypatch.setattr(ws_server.broadcaster, "register", fake_register)
    monkeypatch.setattr(ws_server.broadcaster, "unregister", fake_unregister)

    ws = FakeWebSocket([
        json.dumps({
            "type": "UNEXPECTED_EVENT",
            "payload": {"value": "untrusted"},
        })
    ])

    handler = ws_server.create_handler(FakeBus())
    asyncio.run(handler(ws))

    assert published == []
