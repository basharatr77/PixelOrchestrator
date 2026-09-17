from app.core.module_contract import DeviceState
from app.core.repair_plan import RepairPlan


def test_repair_plan_creates_plan_for_safe_transition():
    plan = RepairPlan.create(
        serial="PIXEL_REPAIR_47C",
        current_state=DeviceState.ADB,
        observed_state=DeviceState.FASTBOOT,
        decision="SAFE_TO_REPAIR",
    )

    assert plan.serial == "PIXEL_REPAIR_47C"
    assert plan.current_state is DeviceState.ADB
    assert plan.observed_state is DeviceState.FASTBOOT
    assert plan.decision == "SAFE_TO_REPAIR"
    assert plan.action == "RECONCILE_STATE"


def test_repair_plan_rejects_unsafe_decision():
    import pytest

    with pytest.raises(ValueError):
        RepairPlan.create(
            serial="PIXEL_REPAIR_47C",
            current_state=DeviceState.ADB,
            observed_state=DeviceState.EDL,
            decision="UNSAFE",
        )
from app.core.module_contract import DeviceState
from app.core.repair_plan import RepairPlan
import pytest


@pytest.mark.parametrize("serial", [None, "", "   "])
def test_repair_plan_rejects_invalid_serial(serial):
    with pytest.raises(ValueError):
        RepairPlan.create(
            serial=serial,
            current_state=DeviceState.ADB,
            observed_state=DeviceState.FASTBOOT,
            decision="SAFE_TO_REPAIR",
        )


@pytest.mark.parametrize("current_state, observed_state", [
    (None, DeviceState.FASTBOOT),
    (DeviceState.ADB, None),
    ("ADB", DeviceState.FASTBOOT),
    (DeviceState.ADB, "FASTBOOT"),
])
def test_repair_plan_rejects_invalid_state_types(current_state, observed_state):
    with pytest.raises(TypeError):
        RepairPlan.create(
            serial="PIXEL_REPAIR_47C",
            current_state=current_state,
            observed_state=observed_state,
            decision="SAFE_TO_REPAIR",
        )


def test_repair_plan_is_immutable():
    plan = RepairPlan.create(
        serial="PIXEL_REPAIR_47C",
        current_state=DeviceState.ADB,
        observed_state=DeviceState.FASTBOOT,
        decision="SAFE_TO_REPAIR",
    )

    with pytest.raises((AttributeError, TypeError)):
        plan.action = "OTHER_ACTION"
