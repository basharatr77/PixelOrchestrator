from dataclasses import dataclass

from app.core.device_registry import DeviceRegistry
from app.core.repair_plan import RepairPlan


@dataclass(frozen=True)
class RepairVerification:
    verified: bool
    expected_state: object
    actual_state: object
    reason: str


class RepairVerifier:
    """Deterministically verify that a repair reached its planned state."""

    @staticmethod
    def verify(plan, registry: DeviceRegistry) -> RepairVerification:
        if not isinstance(plan, RepairPlan):
            return RepairVerification(
                verified=False,
                expected_state=None,
                actual_state=None,
                reason="INVALID_REPAIR_PLAN",
            )

        if not isinstance(registry, DeviceRegistry):
            raise TypeError("registry must be a DeviceRegistry")

        device = registry.get(f"device:{plan.serial}")

        if device is None:
            return RepairVerification(
                verified=False,
                expected_state=plan.observed_state,
                actual_state=None,
                reason="DEVICE_NOT_FOUND",
            )

        if device.state is not plan.observed_state:
            return RepairVerification(
                verified=False,
                expected_state=plan.observed_state,
                actual_state=device.state,
                reason="STATE_MISMATCH",
            )

        return RepairVerification(
            verified=True,
            expected_state=plan.observed_state,
            actual_state=device.state,
            reason="VERIFIED",
        )
