import asyncio
import json

from app.dashboard import ws_server
from app.core.event_bus import StreamBus
from app.core.events import Event


class FakeWebSocket:
    def __init__(self, messages=None):
        self.messages = list(messages or [])
        self.sent = []
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            return self.messages.pop(0)
        raise StopAsyncIteration

    async def send(self, message):
        self.sent.append(message)


def test_event_to_dict_preserves_offset():
    event = Event(
        "DEVICE_CONNECTED",
        {"serial": "PIXEL_8"},
    )

    data = ws_server._event_to_dict(event, 42)

    assert data["id"] == event.id
    assert data["type"] == "DEVICE_CONNECTED"
    assert data["ts"] == event.ts
    assert data["payload"] == {"serial": "PIXEL_8"}
    assert data["offset"] == 42


def test_subscribe_dashboard_registers_expected_event_types():
    bus = StreamBus()

    ws_server.subscribe_dashboard(bus)

    for event_type in ws_server.DASHBOARD_EVENT_TYPES:
        assert len(
            bus.handlers[
                (ws_server.DASHBOARD_GROUP, event_type)
            ]
        ) == 1


def test_replay_dashboard_sends_only_dashboard_events(monkeypatch):
    class FakeLog:
        def read_from(self, offset):
            return [
                {
                    "offset": 11,
                    "id": "event-11",
                    "type": "DEVICE_CONNECTED",
                    "ts": 1.0,
                    "payload": {"serial": "PIXEL_8"},
                },
                {
                    "offset": 12,
                    "id": "event-12",
                    "type": "INTERNAL_EVENT",
                    "ts": 2.0,
                    "payload": {},
                },
                {
                    "offset": 13,
                    "id": "event-13",
                    "type": "TASK_EXECUTED",
                    "ts": 3.0,
                    "payload": {"serial": "PIXEL_8"},
                },
            ]

    monkeypatch.setattr(ws_server, "EventLog", FakeLog)

    async def run():
        ws = FakeWebSocket()

        await ws_server.replay_dashboard(ws, 10)

        assert len(ws.sent) == 2

        first = json.loads(ws.sent[0])
        second = json.loads(ws.sent[1])

        assert first["offset"] == 11
        assert first["type"] == "DEVICE_CONNECTED"

        assert second["offset"] == 13
        assert second["type"] == "TASK_EXECUTED"

    asyncio.run(run())


def test_dashboard_handler_replays_from_last_offset(monkeypatch):
    bus = StreamBus()
    ws = FakeWebSocket([
        json.dumps({
            "type": "dashboard_connect",
            "last_offset": 25,
        })
    ])

    replayed = []

    async def fake_replay(socket, last_offset):
        replayed.append((socket, last_offset))

    monkeypatch.setattr(
        ws_server,
        "replay_dashboard",
        fake_replay,
    )

    registered = []
    unregistered = []

    async def fake_register(socket):
        registered.append(socket)

    async def fake_unregister(socket):
        unregistered.append(socket)

    monkeypatch.setattr(
        ws_server.broadcaster,
        "register",
        fake_register,
    )
    monkeypatch.setattr(
        ws_server.broadcaster,
        "unregister",
        fake_unregister,
    )

    handler = ws_server.create_handler(bus)

    asyncio.run(handler(ws))

    assert replayed == [(ws, 25)]
    assert registered == [ws]
    assert unregistered == [ws]


def test_dashboard_handler_publishes_inbound_event(monkeypatch):
    bus = StreamBus()

    published = []

    async def fake_publish(event):
        published.append(event)

    bus.publish = fake_publish

    ws = FakeWebSocket([
        json.dumps({
            "type": "DEVICE_MODE_CHANGED",
            "payload": {
                "serial": "PIXEL_8",
                "mode": "FASTBOOT",
            },
        })
    ])

    async def fake_register(socket):
        pass

    async def fake_unregister(socket):
        pass

    monkeypatch.setattr(
        ws_server.broadcaster,
        "register",
        fake_register,
    )
    monkeypatch.setattr(
        ws_server.broadcaster,
        "unregister",
        fake_unregister,
    )

    handler = ws_server.create_handler(bus)

    asyncio.run(handler(ws))

    assert len(published) == 1
    assert published[0].type == "DEVICE_MODE_CHANGED"
    assert published[0].payload == {
        "serial": "PIXEL_8",
        "mode": "FASTBOOT",
    }

def test_stream_bus_dispatch_broadcasts_dashboard_event(monkeypatch):
    async def run():
        bus = StreamBus()

        sent = []

        async def fake_broadcast(message):
            sent.append(message)

        monkeypatch.setattr(
            ws_server.broadcaster,
            "broadcast",
            fake_broadcast,
        )

        ws_server.subscribe_dashboard(bus)

        event = Event(
            "DEVICE_CONNECTED",
            {
                "serial": "PIXEL_8",
                "mode": "ADB",
            },
        )

        offset = bus.log.append(event)

        await bus.dispatch(offset, event)

        await asyncio.sleep(0)

        assert sent == [
            {
                "id": event.id,
                "type": "DEVICE_CONNECTED",
                "ts": event.ts,
                "payload": {
                    "serial": "PIXEL_8",
                    "mode": "ADB",
                },
                "offset": offset,
            }
        ]

        assert bus.consumer_store.get_offset(
            ws_server.DASHBOARD_GROUP,
            "DEVICE_CONNECTED",
        ) == offset

    asyncio.run(run())

def test_stream_bus_dispatch_broadcasts_dashboard_event(monkeypatch):
    async def run():
        bus = StreamBus()

        sent = []

        async def fake_broadcast(message):
            sent.append(message)

        monkeypatch.setattr(
            ws_server.broadcaster,
            "broadcast",
            fake_broadcast,
        )

        ws_server.subscribe_dashboard(bus)

        event = Event(
            "DEVICE_CONNECTED",
            {
                "serial": "PIXEL_8",
                "mode": "ADB",
            },
        )

        offset = bus.log.append(event)

        await bus.dispatch(offset, event)

        await asyncio.sleep(0)

        assert sent == [
            {
                "id": event.id,
                "type": "DEVICE_CONNECTED",
                "ts": event.ts,
                "payload": {
                    "serial": "PIXEL_8",
                    "mode": "ADB",
                },
                "offset": offset,
            }
        ]

        assert bus.consumer_store.get_offset(
            ws_server.DASHBOARD_GROUP,
            "DEVICE_CONNECTED",
        ) == offset

    asyncio.run(run())
