import pytest
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

def test_agent_repository_persists_and_reloads_last_seen(tmp_path):
    from app.core.agent_repository import AgentRepository

    db_path = tmp_path / "agents.db"
    repository = AgentRepository(db_path)

    agent = Agent(
        agent_id="agent:presence-001",
        last_seen_at="2026-09-12T00:00:00+00:00",
    )

    repository.save(agent)

    fresh_repository = AgentRepository(db_path)
    fresh_agent = fresh_repository.get("agent:presence-001")

    assert fresh_agent is not None
    assert fresh_agent.agent_id == "agent:presence-001"
    assert fresh_agent.last_seen_at == "2026-09-12T00:00:00+00:00"

def test_agent_repository_migrates_existing_schema_for_last_seen(tmp_path):
    import sqlite3
    from app.core.agent_repository import AgentRepository

    db_path = tmp_path / "agents.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE agents (
                agent_id TEXT PRIMARY KEY
            )
            """
        )
        conn.execute(
            "INSERT INTO agents (agent_id) VALUES (?)",
            ("agent:legacy-001",),
        )

    repository = AgentRepository(db_path)
    agent = repository.get("agent:legacy-001")

    assert agent is not None
    assert agent.agent_id == "agent:legacy-001"
    assert agent.last_seen_at is None

def test_agent_registry_mark_seen_updates_last_seen():
    registry = AgentRegistry()
    agent = Agent(agent_id="agent:presence-002")

    registry.register(agent)
    registry.mark_seen(
        "agent:presence-002",
        "2026-09-12T01:00:00+00:00",
    )

    assert registry.get("agent:presence-002").last_seen_at == (
        "2026-09-12T01:00:00+00:00"
    )

def test_agent_registry_mark_seen_persists_last_seen(tmp_path):
    from app.core.agent_repository import AgentRepository

    db_path = tmp_path / "agents.db"
    repository = AgentRepository(db_path)

    agent = Agent(agent_id="agent:presence-persist-001")
    repository.save(agent)

    registry = AgentRegistry(repository=repository)

    registry.mark_seen(
        "agent:presence-persist-001",
        "2026-09-12T01:30:00+00:00",
    )

    fresh_repository = AgentRepository(db_path)
    fresh_agent = fresh_repository.get("agent:presence-persist-001")

    assert fresh_agent is not None
    assert fresh_agent.last_seen_at == "2026-09-12T01:30:00+00:00"

def test_agent_registry_mark_seen_rejects_unknown_agent():
    registry = AgentRegistry()

    with pytest.raises(
        KeyError,
        match=r"Unknown agent 'agent:presence-unknown-001'\.",
    ):
        registry.mark_seen(
            "agent:presence-unknown-001",
            "2026-09-12T01:45:00+00:00",
        )

def test_agent_registry_agent_is_stale_after_timeout():
    registry = AgentRegistry()
    registry.register(
        Agent(
            agent_id="agent:presence-stale-001",
            last_seen_at="2026-09-12T01:00:00+00:00",
        )
    )

    assert registry.is_stale(
        "agent:presence-stale-001",
        now="2026-09-12T01:05:01+00:00",
        timeout_seconds=300,
    ) is True

def test_agent_registry_agent_is_not_stale_at_exact_timeout():
    registry = AgentRegistry()
    registry.register(
        Agent(
            agent_id="agent:presence-boundary-001",
            last_seen_at="2026-09-12T01:00:00+00:00",
        )
    )

    assert registry.is_stale(
        "agent:presence-boundary-001",
        now="2026-09-12T01:05:00+00:00",
        timeout_seconds=300,
    ) is False

def test_agent_registry_agent_without_last_seen_is_stale():
    registry = AgentRegistry()
    registry.register(
        Agent(agent_id="agent:presence-never-seen-001")
    )

    assert registry.is_stale(
        "agent:presence-never-seen-001",
        now="2026-09-12T01:05:00+00:00",
        timeout_seconds=300,
    ) is True
