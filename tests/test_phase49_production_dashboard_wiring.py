import asyncio

from app.core.agent_device_ownership import AgentDeviceOwnership
from app.core.agent_ownership_repository import AgentOwnershipRepository
from app.core.agent_registry import Agent, AgentRegistry
from app.core.agent_repository import AgentRepository
from app.core.agent_authenticator import ConfiguredAgentAuthenticator
from app.dashboard import ws_server


def test_dashboard_startup_builds_persistent_security_components(
    tmp_path, monkeypatch
):
    database = tmp_path / "dashboard-security.db"

    # Pre-provision one authorized agent and its device ownership.
    agent_repository = AgentRepository(database)
    agent_repository.save(Agent(agent_id="agent-1"))

    ownership_repository = AgentOwnershipRepository(database)
    ownership_repository.save("agent-1", "device:SERIAL-1")

    monkeypatch.setenv(
        ConfiguredAgentAuthenticator.ENV_NAME,
        '{"agent-1":"test-secret"}',
    )

    captured = {}

    def fake_create_handler(bus, **kwargs):
        captured.update(kwargs)
        return object()

    class FakeServer:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def fake_serve(handler, host, port):
        captured["host"] = host
        captured["port"] = port
        return FakeServer()

    async def fake_future():
        return None

    class FakeAsyncio:
        @staticmethod
        def Future():
            return fake_future()

    monkeypatch.setattr(ws_server, "subscribe_dashboard", lambda bus: None)
    monkeypatch.setattr(ws_server, "create_handler", fake_create_handler)
    monkeypatch.setattr(ws_server.websockets, "serve", fake_serve)
    monkeypatch.setattr(ws_server.asyncio, "Future", FakeAsyncio.Future)

    device_registry = object()

    asyncio.run(
        ws_server.run_dashboard(
            object(),
            host="127.0.0.1",
            port=9876,
            database=str(database),
            device_registry=device_registry,
        )
    )

    registry = captured["agent_registry"]
    ownership = captured["ownership"]
    authenticator = captured["authenticator"]

    assert isinstance(registry, AgentRegistry)
    assert registry.get("agent-1") is not None
    assert registry.get("unknown-agent") is None

    assert isinstance(ownership, AgentDeviceOwnership)
    assert ownership.owns("agent-1", "device:SERIAL-1")
    assert not ownership.owns("unknown-agent", "device:SERIAL-1")

    assert authenticator.authenticate(
        "agent-1",
        {"token": "test-secret"},
    )
    assert not authenticator.authenticate(
        "agent-1",
        {"token": "wrong-secret"},
    )

    assert captured["device_registry"] is device_registry
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 9876


def test_dashboard_startup_rejects_invalid_auth_configuration(
    tmp_path, monkeypatch
):
    database = tmp_path / "invalid-dashboard-security.db"

    monkeypatch.setenv(
        ConfiguredAgentAuthenticator.ENV_NAME,
        "{invalid-json",
    )

    monkeypatch.setattr(ws_server, "subscribe_dashboard", lambda bus: None)

    async def scenario():
        await ws_server.run_dashboard(
            object(),
            database=str(database),
            device_registry=object(),
        )

    try:
        asyncio.run(scenario())
    except ValueError as exc:
        assert ConfiguredAgentAuthenticator.ENV_NAME in str(exc)
    else:
        raise AssertionError(
            "Dashboard startup must fail closed for invalid token configuration."
        )
