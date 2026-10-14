import pytest

from app.core.agent_device_ownership import AgentDeviceOwnership


class FailingOwnershipRepository:
    def __init__(self, initial_ownership=()):
        self.initial_ownership = list(initial_ownership)

    def list_all(self):
        return list(self.initial_ownership)

    def save(self, agent_id, device_id):
        raise RuntimeError("simulated save failure")

    def delete(self, agent_id, device_id):
        raise RuntimeError("simulated delete failure")


def test_assign_save_failure_does_not_change_in_memory_ownership():
    repository = FailingOwnershipRepository()
    ownership = AgentDeviceOwnership(repository=repository)

    with pytest.raises(RuntimeError, match="simulated save failure"):
        ownership.assign("agent-001", "device-001")

    assert ownership.owns("agent-001", "device-001") is False
    assert ownership.owner_of("device-001") is None


def test_release_delete_failure_preserves_in_memory_ownership():
    repository = FailingOwnershipRepository(
        initial_ownership=[("agent-001", "device-001")]
    )
    ownership = AgentDeviceOwnership(repository=repository)

    with pytest.raises(RuntimeError, match="simulated delete failure"):
        ownership.release("agent-001", "device-001")

    assert ownership.owns("agent-001", "device-001") is True
    assert ownership.owner_of("device-001") == "agent-001"