import pytest
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

def test_remote_agent_registration_uses_shared_agent_registry():
    async def run():
        from app.core.agent_registry import AgentRegistry

        bus = StreamBus()
        registry = AgentRegistry()

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent-shared-001",
            }),
        ])

        handler = ws_server.create_handler(
            bus,
            agent_registry=registry,
        )
        await handler(ws)

        assert json.loads(ws.sent[0]) == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": "agent-shared-001",
        }

        agent = registry.get("agent-shared-001")

        assert agent is not None
        assert agent.agent_id == "agent-shared-001"
        assert len(registry) == 1

    asyncio.run(run())

def test_remote_agent_cannot_request_unowned_device():
    async def run():
        from app.core.agent_registry import AgentRegistry
        from app.core.device_registry import DeviceRegistry
        from app.core.module_contract import Device, DeviceState, ModuleType

        bus = StreamBus()
        agent_registry = AgentRegistry()
        device_registry = DeviceRegistry()
        from app.core.agent_device_ownership import AgentDeviceOwnership
        ownership = AgentDeviceOwnership()

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": "agent-owner-001",
            }),
            json.dumps({
                "type": "transport_request",
                "request_id": "request-001",
                "operation": "get_device_info",
                "serial": "UNOWNED-DEVICE-001",
                "mode": "ADB",
            }),
        ])

        device_registry.register(
            Device(
                device_id="device:UNOWNED-DEVICE-001",
                module_type=ModuleType.COMMON,
                state=DeviceState.ADB,
                serial="UNOWNED-DEVICE-001",
            )
        )

        handler = ws_server.create_handler(
            bus,
            agent_registry=agent_registry,
            device_registry=device_registry,
            ownership=ownership,
        )

        await handler(ws)

        assert json.loads(ws.sent[0]) == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": "agent-owner-001",
        }

        response = json.loads(ws.sent[1])

        assert response["type"] == "transport_response"
        assert response["request_id"] == "request-001"
        assert response["success"] is False
        assert "ownership" in response["error"].lower()

    asyncio.run(run())
def test_agent_device_ownership_registry_tracks_owned_devices():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")

    assert ownership.owns("agent-001", "device-001") is True
    assert ownership.owns("agent-001", "device-002") is False
    assert ownership.owns("agent-002", "device-001") is False
def test_remote_agent_can_request_owned_device():
    async def run():
        from app.core.agent_device_ownership import AgentDeviceOwnership
        from app.core.agent_registry import AgentRegistry
        from app.core.device_registry import DeviceRegistry
        from app.core.module_contract import Device, DeviceState, ModuleType

        bus = StreamBus()
        agent_registry = AgentRegistry()
        device_registry = DeviceRegistry()
        ownership = AgentDeviceOwnership()

        agent_id = "agent-owner-002"
        serial = "OWNED-DEVICE-001"
        device_id = f"device:{serial}"

        ownership.assign(agent_id, device_id)

        device_registry.register(
            Device(
                device_id=device_id,
                module_type=ModuleType.COMMON,
                state=DeviceState.ADB,
                serial=serial,
            )
        )

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": agent_id,
            }),
            json.dumps({
                "type": "transport_request",
                "request_id": "request-owned-001",
                "operation": "get_device_info",
                "serial": serial,
                "mode": "ADB",
            }),
        ])

        handler = ws_server.create_handler(
            bus,
            agent_registry=agent_registry,
            device_registry=device_registry,
            ownership=ownership,
        )

        await handler(ws)

        assert json.loads(ws.sent[0]) == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": agent_id,
        }

        response = json.loads(ws.sent[1])

        assert response["type"] == "transport_response"
        assert response["request_id"] == "request-owned-001"
        assert response["success"] is True

    asyncio.run(run())

def test_agent_device_ownership_rejects_second_agent_for_same_device():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")

    with pytest.raises(ValueError, match="already owned"):
        ownership.assign("agent-002", "device-001")



def test_agent_device_ownership_allows_same_agent_reassignment():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")
    ownership.assign("agent-001", "device-001")

    assert ownership.owns("agent-001", "device-001")

def test_agent_device_ownership_can_release_owned_device():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")

    assert ownership.release("agent-001", "device-001") is True
    assert ownership.owns("agent-001", "device-001") is False

def test_agent_device_ownership_allows_reclaim_after_release():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")
    assert ownership.release("agent-001", "device-001") is True

    ownership.assign("agent-002", "device-001")

    assert ownership.owns("agent-002", "device-001")

def test_agent_device_ownership_rejects_non_owner_release():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")

    assert ownership.release("agent-002", "device-001") is False
    assert ownership.owns("agent-001", "device-001")

def test_agent_device_ownership_returns_current_owner():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")

    assert ownership.owner_of("device-001") == "agent-001"

def test_agent_device_ownership_returns_none_for_unowned_device():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    assert ownership.owner_of("device-unknown") is None


def test_agent_device_ownership_owner_clears_after_release():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")
    assert ownership.owner_of("device-001") == "agent-001"

    assert ownership.release("agent-001", "device-001") is True
    assert ownership.owner_of("device-001") is None


def test_agent_device_ownership_owner_updates_after_reclaim():
    from app.core.agent_device_ownership import AgentDeviceOwnership

    ownership = AgentDeviceOwnership()

    ownership.assign("agent-001", "device-001")
    assert ownership.owner_of("device-001") == "agent-001"

    assert ownership.release("agent-001", "device-001") is True

    ownership.assign("agent-002", "device-001")

    assert ownership.owner_of("device-001") == "agent-002"


def test_remote_agent_cannot_request_owned_but_unregistered_device():
    async def run():
        from app.core.agent_device_ownership import AgentDeviceOwnership
        from app.core.agent_registry import AgentRegistry
        from app.core.device_registry import DeviceRegistry

        bus = StreamBus()
        agent_registry = AgentRegistry()
        device_registry = DeviceRegistry()
        ownership = AgentDeviceOwnership()

        agent_id = "agent-owner-003"
        serial = "MISSING-DEVICE-001"
        device_id = f"device:{serial}"

        ownership.assign(agent_id, device_id)

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": agent_id,
            }),
            json.dumps({
                "type": "transport_request",
                "request_id": "request-missing-device-001",
                "operation": "get_device_info",
                "serial": serial,
                "mode": "ADB",
            }),
        ])

        handler = ws_server.create_handler(
            bus,
            agent_registry=agent_registry,
            device_registry=device_registry,
            ownership=ownership,
        )

        await handler(ws)

        assert json.loads(ws.sent[0]) == {
            "type": "agent_register_response",
            "success": True,
            "agent_id": agent_id,
        }

        response = json.loads(ws.sent[1])

        assert response["type"] == "transport_response"
        assert response["request_id"] == "request-missing-device-001"
        assert response["success"] is False
        assert "device" in response["error"].lower()

    asyncio.run(run())
