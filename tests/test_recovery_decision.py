from app.core.module_contract import DeviceState
from app.core.recovery_decision import RecoveryDecision


def test_recovery_decision_allows_known_safe_transition():
    decision = RecoveryDecision.decide(
        DeviceState.ADB,
        DeviceState.FASTBOOT,
    )

    assert decision == "SAFE_TO_REPAIR"


def test_recovery_decision_rejects_unknown_transition():
    decision = RecoveryDecision.decide(
        DeviceState.ADB,
        DeviceState.UNKNOWN,
    )

    assert decision == "UNKNOWN"
from app.core.module_contract import DeviceState
from app.core.recovery_decision import RecoveryDecision
import pytest


def test_recovery_decision_marks_unsafe_transition():
    decision = RecoveryDecision.decide(
        DeviceState.ADB,
        DeviceState.EDL,
    )

    assert decision == "UNSAFE"


@pytest.mark.parametrize("current, observed", [
    (None, DeviceState.ADB),
    (DeviceState.ADB, None),
    ("ADB", DeviceState.FASTBOOT),
    (DeviceState.ADB, "FASTBOOT"),
])
def test_recovery_decision_rejects_invalid_state_types(current, observed):
    with pytest.raises(TypeError):
        RecoveryDecision.decide(current, observed)
