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

def test_agent_repository_persists_and_reloads_agent(tmp_path):
    from app.core.agent_repository import AgentRepository

    db_path = tmp_path / "agents.db"
    repository = AgentRepository(db_path)

    repository.save(Agent(agent_id="agent:persist-001"))

    fresh_repository = AgentRepository(db_path)

    agent = fresh_repository.get("agent:persist-001")

    assert agent is not None
    assert agent.agent_id == "agent:persist-001"

def test_agent_repository_rejects_non_agent(tmp_path):
    from app.core.agent_repository import AgentRepository

    repository = AgentRepository(tmp_path / "agents.db")

    try:
        repository.save(object())
    except TypeError:
        pass
    else:
        raise AssertionError("Non-Agent persistence must be rejected")

def test_agent_repository_rejects_duplicate_identity(tmp_path):
    from app.core.agent_repository import AgentRepository

    repository = AgentRepository(tmp_path / "agents.db")
    agent = Agent(agent_id="agent:persist-002")

    repository.save(agent)

    try:
        repository.save(agent)
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Duplicate agent_id must be rejected")

def test_agent_registry_reloads_persisted_agents(tmp_path):
    from app.core.agent_registry import Agent, AgentRegistry
    from app.core.agent_repository import AgentRepository

    db_path = tmp_path / "agents.db"
    repository = AgentRepository(db_path)

    repository.save(Agent(agent_id="agent:restart-001"))

    fresh_registry = AgentRegistry(repository=AgentRepository(db_path))

    agent = fresh_registry.get("agent:restart-001")

    assert agent is not None
    assert agent.agent_id == "agent:restart-001"
