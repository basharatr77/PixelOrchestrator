from app.core.agent_registry import Agent, AgentRegistry


def test_agent_has_stable_identity():
    agent = Agent(agent_id="agent:test-001")

    assert agent.agent_id == "agent:test-001"


def test_agent_registry_registers_and_retrieves_agent():
    registry = AgentRegistry()
    agent = Agent(agent_id="agent:test-001")

    registry.register(agent)

    assert registry.get("agent:test-001") is agent
    assert registry.contains("agent:test-001")
    assert len(registry) == 1


def test_agent_registry_rejects_duplicate_identity():
    registry = AgentRegistry()

    registry.register(Agent(agent_id="agent:test-001"))

    try:
        registry.register(Agent(agent_id="agent:test-001"))
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate agent_id must be rejected")

def test_agent_registry_rejects_non_agent():
    registry = AgentRegistry()

    try:
        registry.register(object())
    except TypeError:
        pass
    else:
        raise AssertionError("Non-Agent registration must be rejected")


def test_agent_registry_remove():
    registry = AgentRegistry()
    agent = Agent(agent_id="agent:test-002")

    registry.register(agent)

    assert registry.remove("agent:test-002") is True
    assert registry.get("agent:test-002") is None
    assert registry.contains("agent:test-002") is False
    assert registry.remove("agent:test-002") is False


def test_agent_registry_snapshot_is_isolated():
    registry = AgentRegistry()
    agent = Agent(agent_id="agent:test-003")

    registry.register(agent)

    snapshot = registry.snapshot()
    snapshot.clear()

    assert registry.contains("agent:test-003")
    assert len(registry) == 1


def test_agent_registry_clear():
    registry = AgentRegistry()

    registry.register(Agent(agent_id="agent:test-004"))
    registry.register(Agent(agent_id="agent:test-005"))

    registry.clear()

    assert len(registry) == 0
    assert registry.get("agent:test-004") is None
    assert registry.get("agent:test-005") is None
