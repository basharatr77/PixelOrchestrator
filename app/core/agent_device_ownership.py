"""Canonical agent-to-device ownership registry."""


class AgentDeviceOwnership:
    """In-memory mapping of agents to owned device IDs."""

    def __init__(self, repository=None) -> None:
        self._ownership: dict[str, set[str]] = {}
        self._repository = repository

        if repository is not None:
            for agent_id, device_id in repository.list_all():
                self._ownership.setdefault(agent_id, set()).add(device_id)

    def assign(self, agent_id: str, device_id: str) -> None:
        current_owner = next(
            (
                owner_id
                for owner_id, device_ids in self._ownership.items()
                if device_id in device_ids
            ),
            None,
        )

        if current_owner is not None and current_owner != agent_id:
            raise ValueError(
                f"Device '{device_id}' is already owned by agent '{current_owner}'."
            )

        if device_id in self._ownership.get(agent_id, set()):
            return

        self._ownership.setdefault(agent_id, set()).add(device_id)

        if self._repository is not None:
            self._repository.save(agent_id, device_id)

    def owns(self, agent_id: str, device_id: str) -> bool:
        return device_id in self._ownership.get(agent_id, set())

    def release(self, agent_id: str, device_id: str) -> bool:
        device_ids = self._ownership.get(agent_id)

        if device_ids is None or device_id not in device_ids:
            return False

        device_ids.remove(device_id)

        if not device_ids:
            del self._ownership[agent_id]

        if self._repository is not None:
            self._repository.delete(agent_id, device_id)

        return True

    def owner_of(self, device_id: str) -> str | None:
        return next(
            (
                agent_id
                for agent_id, device_ids in self._ownership.items()
                if device_id in device_ids
            ),
            None,
        )
