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


class AllowingAuthenticator:
    def authenticate(self, agent_id, data):
        return True


def test_remote_agent_connection_is_released_after_handler_exit():
    async def run():
        from app.core.agent_registry import AgentRegistry

        bus = StreamBus()
        agent_registry = AgentRegistry()
        agent_id = "agent:step22-cleanup-001"

        agent_registry.register(
            ws_server.Agent(agent_id=agent_id)
        )

        ws = FakeWebSocket([
            json.dumps({
                "type": "agent_register",
                "agent_id": agent_id,
            }),
        ])

        handler = ws_server.create_handler(
            bus,
            agent_registry=agent_registry,
            authenticator=AllowingAuthenticator(),
        )

        await handler(ws)

        assert agent_registry.is_connection_current(
            agent_id,
            "connection-after-handler-exit",
        ) is False

    asyncio.run(run())
