from dataclasses import dataclass

from app.core.module_contract import DeviceState


@dataclass(frozen=True)
class RepairPlan:
    """Deterministic repair intent produced after recovery decision."""

    serial: str
    current_state: DeviceState
    observed_state: DeviceState
    decision: str
    action: str

    @classmethod
    def create(
        cls,
        serial: str,
        current_state: DeviceState,
        observed_state: DeviceState,
        decision: str,
    ):
        if not isinstance(serial, str) or not serial.strip():
            raise ValueError("serial must be a non-empty string")

        if not isinstance(current_state, DeviceState):
            raise TypeError("current_state must be a DeviceState")

        if not isinstance(observed_state, DeviceState):
            raise TypeError("observed_state must be a DeviceState")

        if decision != "SAFE_TO_REPAIR":
            raise ValueError(
                f"Repair plan cannot be created for decision '{decision}'."
            )

        return cls(
            serial=serial,
            current_state=current_state,
            observed_state=observed_state,
            decision=decision,
            action="RECONCILE_STATE",
        )
