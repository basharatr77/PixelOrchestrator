from app.core.module_contract import Device, DeviceState, ModuleType
from app.modules.common.module import CommonModule


def test_common_module_reconcile_state_transitions_device():
    module = CommonModule()
    device = Device(
        device_id="device:PIXEL_8",
        module_type=ModuleType.COMMON,
        state=DeviceState.ADB,
        serial="PIXEL_8",
    )

    result = module.execute(
        "reconcile_state",
        device=device,
        target_state=DeviceState.FASTBOOT,
    )

    assert result.success is True
    assert device.state is DeviceState.FASTBOOT
from app.core.module_contract import Device, DeviceState, ModuleType
from app.modules.common.module import CommonModule


def make_device(state):
    return Device(
        device_id="device:PIXEL_8",
        module_type=ModuleType.COMMON,
        state=state,
        serial="PIXEL_8",
    )


def test_common_module_reconcile_state_requires_device():
    result = CommonModule().execute(
        "reconcile_state",
        target_state=DeviceState.FASTBOOT,
    )

    assert result.success is False
    assert result.error_code == "DEVICE_REQUIRED"


def test_common_module_reconcile_state_requires_target_state():
    result = CommonModule().execute(
        "reconcile_state",
        device=make_device(DeviceState.ADB),
    )

    assert result.success is False
    assert result.error_code == "TARGET_STATE_REQUIRED"


def test_common_module_reconcile_state_rejects_unsafe_transition():
    device = make_device(DeviceState.EDL)

    result = CommonModule().execute(
        "reconcile_state",
        device=device,
        target_state=DeviceState.ADB,
    )

    assert result.success is False
    assert result.error_code == "INVALID_STATE_TRANSITION"
    assert device.state is DeviceState.EDL
