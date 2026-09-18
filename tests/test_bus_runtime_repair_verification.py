from app.core.bus_runtime import BusRuntime
from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.repair_plan import RepairPlan
from app.core.repair_verifier import RepairVerification


def test_bus_runtime_execute_repair_returns_verified_result():
    runtime = BusRuntime()

    runtime.task_executor.module_registry.register(
        __import__(
            "app.modules.common.module",
            fromlist=["CommonModule"],
        ).CommonModule()
    )

    runtime.device_registry.register(
        Device(
            device_id="device:PIXEL_VERIFY_RUNTIME",
            module_type=ModuleType.COMMON,
            state=DeviceState.ADB,
            serial="PIXEL_VERIFY_RUNTIME",
        )
    )

    plan = RepairPlan.create(
        serial="PIXEL_VERIFY_RUNTIME",
        current_state=DeviceState.ADB,
        observed_state=DeviceState.FASTBOOT,
        decision="SAFE_TO_REPAIR",
    )

    verification = runtime.execute_repair(plan)

    assert isinstance(verification, RepairVerification)
    assert verification.verified is True
    assert verification.expected_state is DeviceState.FASTBOOT
    assert verification.actual_state is DeviceState.FASTBOOT


def test_bus_runtime_execute_repair_rejects_invalid_plan():
    runtime = BusRuntime()

    verification = runtime.execute_repair(None)

    assert isinstance(verification, RepairVerification)
    assert verification.verified is False
    assert verification.reason == "INVALID_REPAIR_PLAN"

def test_bus_runtime_execute_repair_reports_failed_verification():
    runtime = BusRuntime()

    runtime.task_executor.module_registry.register(
        __import__(
            "app.modules.common.module",
            fromlist=["CommonModule"],
        ).CommonModule()
    )

    runtime.device_registry.register(
        Device(
            device_id="device:PIXEL_VERIFY_FAILURE",
            module_type=ModuleType.COMMON,
            state=DeviceState.EDL,
            serial="PIXEL_VERIFY_FAILURE",
        )
    )

    plan = RepairPlan.create(
        serial="PIXEL_VERIFY_FAILURE",
        current_state=DeviceState.ADB,
        observed_state=DeviceState.FASTBOOT,
        decision="SAFE_TO_REPAIR",
    )

    verification = runtime.execute_repair(plan)

    assert isinstance(verification, RepairVerification)
    assert verification.verified is False
    assert verification.expected_state is DeviceState.FASTBOOT
    assert verification.actual_state is DeviceState.EDL
    assert verification.reason == "STATE_MISMATCH"
