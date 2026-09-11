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

def test_dashboard_handler_ignores_non_object_json_and_continues(monkeypatch):
    bus = StreamBus()

    async def fake_register(socket):
        pass

    async def fake_unregister(socket):
        pass

    async def fake_handle_transport_request(socket, data, device_registry=None, ownership=None, agent_id=None):
        await socket.send(json.dumps({
            "type": "transport_response",
            "request_id": data["request_id"],
            "success": True,
            "result": {"device": "ok"},
        }))

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
    monkeypatch.setattr(
        ws_server,
        "handle_transport_request",
        fake_handle_transport_request,
    )

    ws = FakeWebSocket([
        json.dumps([]),
        json.dumps({
            "type": "agent_register",
            "agent_id": "agent-test-non-object",
        }),
        json.dumps({
            "type": "transport_request",
            "request_id": "after-non-object",
            "operation": "get_device_info",
            "serial": "TEST123",
            "mode": "ADB",
        }),
    ])

    handler = ws_server.create_handler(bus)

    asyncio.run(handler(ws))

    assert len(ws.sent) == 2

    registration_response = json.loads(ws.sent[0])
    response = json.loads(ws.sent[1])

    assert registration_response == {
        "type": "agent_register_response",
        "success": True,
        "agent_id": "agent-test-non-object",
    }

    assert response["type"] == "transport_response"
    assert response["request_id"] == "after-non-object"
    assert response["success"] is True


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

def test_dashboard_handler_same_agent_new_connection_supersedes_old_connection(
    monkeypatch,
):
    bus = StreamBus()

    async def fake_register(socket):
        pass

    async def fake_unregister(socket):
        pass

    monkeypatch.setattr(ws_server.broadcaster, "register", fake_register)
    monkeypatch.setattr(ws_server.broadcaster, "unregister", fake_unregister)

    agent_registry = ws_server.AgentRegistry()
    first_claimed = asyncio.Event()
    release_first = asyncio.Event()
    second_claimed = asyncio.Event()
    release_second = asyncio.Event()

    original_claim = agent_registry.claim_connection

    def claim_connection(agent_id, connection_id):
        result = original_claim(agent_id, connection_id)
        if connection_id == str(id(first_ws)):
            first_claimed.set()
        elif connection_id == str(id(second_ws)):
            second_claimed.set()
        return result

    monkeypatch.setattr(agent_registry, "claim_connection", claim_connection)

    class CoordinatedWebSocket(FakeWebSocket):
        def __init__(self, messages, release_event):
            super().__init__(messages)
            self.release_event = release_event

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.messages:
                return self.messages.pop(0)
            await self.release_event.wait()
            raise StopAsyncIteration

    first_ws = CoordinatedWebSocket(
        [
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent:multi-001",
            }),
        ],
        release_first,
    )

    second_ws = CoordinatedWebSocket(
        [
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent:multi-001",
            }),
        ],
        release_second,
    )

    async def run():
        handler = ws_server.create_handler(
            bus,
            agent_registry=agent_registry,
        )

        first_task = asyncio.create_task(handler(first_ws))
        await first_claimed.wait()

        second_task = asyncio.create_task(handler(second_ws))
        await second_claimed.wait()

        assert agent_registry.is_connection_current(
            "agent:multi-001",
            str(id(second_ws)),
        ) is True

        release_first.set()
        await first_task

        assert agent_registry.is_connection_current(
            "agent:multi-001",
            str(id(second_ws)),
        ) is True

        release_second.set()
        await second_task

    asyncio.run(run())
