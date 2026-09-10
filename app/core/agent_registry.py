"""Canonical remote-agent identity registry."""

from dataclasses import dataclass


@dataclass
class Agent:
    """Canonical remote-agent representation."""

    agent_id: str


class AgentRegistry:
    """In-memory registry of canonical remote agents."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

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
