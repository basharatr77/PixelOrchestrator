import asyncio
import json

from app.core.event_bus import StreamBus
from app.dashboard import ws_server


class StaleConnectionWebSocket:
    def __init__(self, messages, agent_registry, agent_id):
        self.messages = iter(messages)
        self.sent = []
        self.agent_registry = agent_registry
        self.agent_id = agent_id
        self.message_count = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            message = next(self.messages)
        except StopIteration:
            raise StopAsyncIteration

        self.message_count += 1

        if self.message_count == 2:
            self.agent_registry.claim_connection(
                self.agent_id,
                "connection-from-reconnect",
            )

        return message

    async def send(self, message):
        self.sent.append(message)


class AllowingAuthenticator:
    def authenticate(self, agent_id, data):
        return True


def test_stale_remote_agent_connection_is_rejected_after_reconnect():
    async def run():
        from app.core.agent_device_ownership import AgentDeviceOwnership
        from app.core.agent_registry import AgentRegistry
        from app.core.device_registry import DeviceRegistry
        from app.core.module_contract import Device, DeviceState, ModuleType

        bus = StreamBus()
        agent_registry = AgentRegistry()
        device_registry = DeviceRegistry()
        ownership = AgentDeviceOwnership()

        agent_id = "agent:step22-stale-001"
        serial = "STEP22-STALE-001"
        device_id = f"device:{serial}"

        agent_registry.register(
            ws_server.Agent(agent_id=agent_id)
        )

        device_registry.register(
            Device(
                device_id=device_id,
                module_type=ModuleType.COMMON,
                state=DeviceState.ADB,
                serial=serial,
            )
        )

        ownership.assign(agent_id, device_id)

        ws = StaleConnectionWebSocket(
            [
                json.dumps({
                    "type": "agent_register",
                    "agent_id": agent_id,
                }),
                json.dumps({
                    "type": "transport_request",
                    "request_id": "step22-stale-request-001",
                    "operation": "get_device_info",
                    "serial": serial,
                    "mode": "ADB",
                }),
            ],
            agent_registry,
            agent_id,
        )

        handler = ws_server.create_handler(
            bus,
            agent_registry=agent_registry,
            device_registry=device_registry,
            ownership=ownership,
            authenticator=AllowingAuthenticator(),
        )

        await handler(ws)

        response = json.loads(ws.sent[-1])

        assert response == {
            "type": "transport_response",
            "request_id": "step22-stale-request-001",
            "success": False,
            "error": "agent connection is no longer current",
        }

    asyncio.run(run())
