from app.core.device_state import DeviceStateMachine
from app.core.module_contract import DeviceState


class RecoveryDecision:
    """Deterministically decide whether a device state drift is repairable."""

    @classmethod
    def decide(cls, current: DeviceState, observed: DeviceState) -> str:
        if not isinstance(current, DeviceState):
            raise TypeError("current must be a DeviceState")

        if not isinstance(observed, DeviceState):
            raise TypeError("observed must be a DeviceState")

        if current is DeviceState.UNKNOWN or observed is DeviceState.UNKNOWN:
            return "UNKNOWN"

        if observed in DeviceStateMachine.VALID_TRANSITIONS.get(current, set()):
            return "SAFE_TO_REPAIR"

        return "UNSAFE"
