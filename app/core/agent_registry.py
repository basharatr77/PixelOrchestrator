"""Canonical remote-agent identity registry."""

from dataclasses import dataclass


@dataclass
class Agent:
    """Canonical remote-agent representation."""

    agent_id: str
    last_seen_at: str | None = None


class AgentRegistry:
    """In-memory registry of canonical remote agents."""

    def __init__(self, repository=None) -> None:
        self._agents: dict[str, Agent] = {}
        self._active_connections: dict[str, str] = {}
        self._repository = repository

        if repository is not None:
            for agent_id in repository.list_ids():
                agent = repository.get(agent_id)
                if agent is not None:
                    self._agents[agent.agent_id] = agent

    def register(self, agent: Agent) -> None:
        if not isinstance(agent, Agent):
            raise TypeError("Agent must be a canonical Agent.")

        agent_id = agent.agent_id

        if agent_id in self._agents:
            raise ValueError(
                f"Agent '{agent_id}' is already registered."
            )

        self._agents[agent_id] = agent

    def get(self, agent_id: str) -> Agent | None:
        return self._agents.get(agent_id)

    def claim_connection(self, agent_id: str, connection_id: str) -> bool:
        agent = self._agents.get(agent_id)

        if agent is None:
            raise KeyError(f"Unknown agent '{agent_id}'.")

        self._active_connections[agent_id] = connection_id
        return True

    def is_connection_current(
        self,
        agent_id: str,
        connection_id: str,
    ) -> bool:
        if agent_id not in self._agents:
            raise KeyError(f"Unknown agent '{agent_id}'.")

        return self._active_connections.get(agent_id) == connection_id

    def release_connection(
        self,
        agent_id: str,
        connection_id: str,
    ) -> bool:
        if agent_id not in self._agents:
            raise KeyError(f"Unknown agent '{agent_id}'.")

        if self._active_connections.get(agent_id) != connection_id:
            return False

        del self._active_connections[agent_id]
        return True

    def mark_seen(self, agent_id: str, last_seen_at: str) -> None:
        agent = self._agents.get(agent_id)

        if agent is None:
            raise KeyError(f"Unknown agent '{agent_id}'.")

        agent.last_seen_at = last_seen_at

        if self._repository is not None:
            self._repository.update_last_seen(
                agent_id,
                last_seen_at,
            )

    def is_stale(
        self,
        agent_id: str,
        now: str,
        timeout_seconds: int,
    ) -> bool:
        agent = self._agents.get(agent_id)

        if agent is None:
            raise KeyError(f"Unknown agent '{agent_id}'.")

        if agent.last_seen_at is None:
            return True

        from datetime import datetime

        last_seen = datetime.fromisoformat(agent.last_seen_at)
        current = datetime.fromisoformat(now)

        return (current - last_seen).total_seconds() > timeout_seconds

    def contains(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def remove(self, agent_id: str) -> bool:
        return self._agents.pop(agent_id, None) is not None

    def snapshot(self) -> dict[str, Agent]:
        return dict(self._agents)

    def clear(self) -> None:
        self._agents.clear()

    def __len__(self) -> int:
        return len(self._agents)
