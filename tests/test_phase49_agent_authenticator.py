import json

import pytest

from app.core.agent_authenticator import ConfiguredAgentAuthenticator


def test_authenticator_accepts_configured_agent_token():
    auth = ConfiguredAgentAuthenticator({"agent-1": "secret-token"})

    assert auth.authenticate(
        "agent-1",
        {"type": "agent_register", "token": "secret-token"},
    ) is True


@pytest.mark.parametrize(
    ("agent_id", "data"),
    [
        ("unknown-agent", {"token": "secret-token"}),
        ("agent-1", {}),
        ("agent-1", {"token": ""}),
        ("agent-1", {"token": "wrong-token"}),
        ("", {"token": "secret-token"}),
        ("agent-1", None),
    ],
)
def test_authenticator_rejects_unknown_or_invalid_credentials(agent_id, data):
    auth = ConfiguredAgentAuthenticator({"agent-1": "secret-token"})

    assert auth.authenticate(agent_id, data) is False


@pytest.mark.parametrize(
    "tokens",
    [
        [],
        {"": "secret"},
        {"agent-1": ""},
        {"agent-1": None},
        {1: "secret"},
    ],
)
def test_authenticator_rejects_invalid_token_configuration(tokens):
    with pytest.raises(ValueError):
        ConfiguredAgentAuthenticator(tokens)


def test_authenticator_loads_tokens_from_environment(monkeypatch):
    monkeypatch.setenv(
        "PIXEL_ORCHESTRATOR_AGENT_TOKENS",
        json.dumps({"agent-2": "another-secret"}),
    )

    auth = ConfiguredAgentAuthenticator.from_environment()

    assert auth.authenticate("agent-2", {"token": "another-secret"}) is True


def test_authenticator_fails_closed_on_invalid_environment_json(monkeypatch):
    monkeypatch.setenv("PIXEL_ORCHESTRATOR_AGENT_TOKENS", "{invalid")

    with pytest.raises(ValueError, match="valid JSON"):
        ConfiguredAgentAuthenticator.from_environment()


def test_authenticator_with_missing_environment_configuration_rejects_all(
    monkeypatch,
):
    monkeypatch.delenv("PIXEL_ORCHESTRATOR_AGENT_TOKENS", raising=False)

    auth = ConfiguredAgentAuthenticator.from_environment()

    assert auth.authenticate("agent-1", {"token": "anything"}) is False
