"""Canonical agent-to-device ownership registry."""

class AgentDeviceOwnership:
    """In-memory mapping of agents to owned device IDs."""

    def __init__(self) -> None:
        self._ownership: dict[str, set[str]] = {}

    def assign(self, agent_id: str, device_id: str) -> None:
        self._ownership.setdefault(agent_id, set()).add(device_id)

    def owns(self, agent_id: str, device_id: str) -> bool:
        return device_id in self._ownership.get(agent_id, set())
