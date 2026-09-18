from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.repair_plan import RepairPlan
from app.core.repair_verifier import RepairVerifier


def make_registry(state=DeviceState.ADB, serial="PIXEL_VERIFY_8"):
    registry = DeviceRegistry()
    registry.register(
        Device(
            device_id=f"device:{serial}",
            module_type=ModuleType.COMMON,
            state=state,
            serial=serial,
        )
    )
    return registry


def make_plan(
    serial="PIXEL_VERIFY_8",
    current_state=DeviceState.ADB,
    observed_state=DeviceState.FASTBOOT,
):
    return RepairPlan.create(
        serial=serial,
        current_state=current_state,
        observed_state=observed_state,
        decision="SAFE_TO_REPAIR",
    )


def test_repair_verifier_confirms_expected_state():
    registry = make_registry(state=DeviceState.FASTBOOT)
    plan = make_plan()

    result = RepairVerifier.verify(plan, registry)

    assert result.verified is True
    assert result.expected_state is DeviceState.FASTBOOT
    assert result.actual_state is DeviceState.FASTBOOT


def test_repair_verifier_rejects_state_mismatch():
    registry = make_registry(state=DeviceState.ADB)
    plan = make_plan()

    result = RepairVerifier.verify(plan, registry)

    assert result.verified is False
    assert result.expected_state is DeviceState.FASTBOOT
    assert result.actual_state is DeviceState.ADB


def test_repair_verifier_rejects_missing_device():
    registry = DeviceRegistry()
    plan = make_plan()

    result = RepairVerifier.verify(plan, registry)

    assert result.verified is False
    assert result.actual_state is None


def test_repair_verifier_rejects_invalid_plan():
    registry = make_registry()

    result = RepairVerifier.verify(None, registry)

    assert result.verified is False
