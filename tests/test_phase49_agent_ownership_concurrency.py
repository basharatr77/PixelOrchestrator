from threading import Barrier, BrokenBarrierError, Thread

from app.core.agent_device_ownership import AgentDeviceOwnership


def test_concurrent_claims_cannot_assign_one_device_to_two_agents():
    ownership = AgentDeviceOwnership()
    both_checked = Barrier(2)

    class CoordinatedOwnership(dict):
        def items(self):
            snapshot = tuple(super().items())
            try:
                both_checked.wait(timeout=0.5)
            except BrokenBarrierError:
                pass
            return snapshot

    # Hold both claims immediately after their ownership snapshots so the
    # check-then-mutate race is deterministic without relying on timing.
    ownership._ownership = CoordinatedOwnership()
    outcomes = []

    def claim(agent_id):
        try:
            ownership.assign(agent_id, "device:shared")
        except ValueError:
            outcomes.append((agent_id, "rejected"))
        else:
            outcomes.append((agent_id, "assigned"))

    threads = [
        Thread(target=claim, args=(agent_id,))
        for agent_id in ("agent:first", "agent:second")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)

    assert all(not thread.is_alive() for thread in threads)
    assert sorted(result for _, result in outcomes) == ["assigned", "rejected"]
    assert sum(
        ownership.owns(agent_id, "device:shared")
        for agent_id in ("agent:first", "agent:second")
    ) == 1
