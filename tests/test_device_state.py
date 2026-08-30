from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.device_state import DeviceStateMachine


def make_device(state):
    return Device(
        device_id="adb:PIXEL_8",
        module_type=ModuleType.ADB,
        state=state,
        serial="PIXEL_8",
        transport="adb",
    )


def test_unknown_to_adb():
    device = make_device(DeviceState.UNKNOWN)

    DeviceStateMachine.transition(device, DeviceState.ADB)

    assert device.state is DeviceState.ADB


def test_disconnected_to_adb():
    device = make_device(DeviceState.DISCONNECTED)

    DeviceStateMachine.transition(device, DeviceState.ADB)

    assert device.state is DeviceState.ADB


def test_adb_to_fastboot():
    device = make_device(DeviceState.ADB)

    DeviceStateMachine.transition(device, DeviceState.FASTBOOT)

    assert device.state is DeviceState.FASTBOOT


def test_fastboot_to_fastbootd():
    device = make_device(DeviceState.FASTBOOT)

    DeviceStateMachine.transition(device, DeviceState.FASTBOOTD)

    assert device.state is DeviceState.FASTBOOTD


def test_recovery_to_sideload():
    device = make_device(DeviceState.RECOVERY)

    DeviceStateMachine.transition(device, DeviceState.SIDELOAD)

    assert device.state is DeviceState.SIDELOAD


def test_adb_to_disconnected():
    device = make_device(DeviceState.ADB)

    DeviceStateMachine.transition(device, DeviceState.DISCONNECTED)

    assert device.state is DeviceState.DISCONNECTED


def test_invalid_transition_is_rejected():
    device = make_device(DeviceState.EDL)

    try:
        DeviceStateMachine.transition(device, DeviceState.ADB)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid transition was accepted")


def test_failed_transition_preserves_state():
    device = make_device(DeviceState.EDL)

    try:
        DeviceStateMachine.transition(device, DeviceState.ADB)
    except ValueError:
        pass

    assert device.state is DeviceState.EDL
