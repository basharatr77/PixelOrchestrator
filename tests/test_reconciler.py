from app.core.device_registry import DeviceRegistry
from app.core.module_contract import Device, DeviceState, ModuleType


def test_reconciliation_detects_canonical_state_drift():
    registry = DeviceRegistry()

    registry.register(
        Device(
            device_id="device:PIXEL_8",
            module_type=ModuleType.ADB,
            state=DeviceState.ADB,
            serial="PIXEL_8",
            transport="adb",
        )
    )

    observed = {
        "PIXEL_8": "FASTBOOT",
    }

    from app.core.reconciler import Reconciler

    reconciler = Reconciler(registry)
    changes = reconciler.reconcile(observed)

    assert changes == [
        {
            "serial": "PIXEL_8",
            "previous_state": DeviceState.ADB,
            "state": DeviceState.FASTBOOT,
        }
    ]

def test_reconciliation_reports_observed_device_missing_from_registry():
    registry = DeviceRegistry()

    observed = {
        "PIXEL_9": "ADB",
    }

    from app.core.reconciler import Reconciler

    reconciler = Reconciler(registry)
    changes = reconciler.reconcile(observed)

    assert changes == [
        {
            "serial": "PIXEL_9",
            "previous_state": None,
            "state": DeviceState.ADB,
        }
    ]

def test_reconciliation_does_not_report_missing_observation_as_disconnect():
    registry = DeviceRegistry()

    registry.register(
        Device(
            device_id="device:PIXEL_8",
            module_type=ModuleType.ADB,
            state=DeviceState.ADB,
            serial="PIXEL_8",
            transport="adb",
        )
    )

    observed = {}

    from app.core.reconciler import Reconciler

    reconciler = Reconciler(registry)
    changes = reconciler.reconcile(observed)

    assert changes == []

def test_reconciliation_ignores_unknown_observed_mode():
    registry = DeviceRegistry()

    registry.register(
        Device(
            device_id="device:PIXEL_8",
            module_type=ModuleType.ADB,
            state=DeviceState.ADB,
            serial="PIXEL_8",
            transport="adb",
        )
    )

    observed = {
        "PIXEL_8": "UNKNOWN_MODE",
    }

    from app.core.reconciler import Reconciler

    reconciler = Reconciler(registry)
    changes = reconciler.reconcile(observed)

    assert changes == []

import pytest


@pytest.mark.parametrize(
    "observed",
    [
        None,
        [],
        "PIXEL_8",
    ],
)
def test_reconciliation_rejects_non_dict_observation(observed):
    registry = DeviceRegistry()

    from app.core.reconciler import Reconciler

    reconciler = Reconciler(registry)

    with pytest.raises(TypeError, match="observed must be a dict"):
        reconciler.reconcile(observed)

@pytest.mark.parametrize(
    "registry",
    [
        None,
        {},
        [],
        "registry",
    ],
)
def test_reconciler_rejects_invalid_registry(registry):
    from app.core.reconciler import Reconciler

    with pytest.raises(TypeError, match="registry must be a DeviceRegistry"):
        Reconciler(registry)

def test_reconciliation_applies_observed_state_to_registry():
    registry = DeviceRegistry()

    registry.register(
        Device(
            device_id="device:PIXEL_8",
            module_type=ModuleType.ADB,
            state=DeviceState.ADB,
            serial="PIXEL_8",
            transport="adb",
        )
    )

    from app.core.reconciler import Reconciler

    reconciler = Reconciler(registry)
    changes = reconciler.reconcile({"PIXEL_8": "FASTBOOT"})

    assert changes == [
        {
            "serial": "PIXEL_8",
            "previous_state": DeviceState.ADB,
            "state": DeviceState.FASTBOOT,
        }
    ]
    assert registry.get("device:PIXEL_8").state == DeviceState.FASTBOOT

def test_reconciliation_can_detect_without_applying_observed_state():
    registry = DeviceRegistry()
    registry.register(
        Device(
            device_id="device:PIXEL_8",
            module_type=ModuleType.ADB,
            state=DeviceState.ADB,
            serial="PIXEL_8",
        )
    )

    from app.core.reconciler import Reconciler

    reconciler = Reconciler(registry)
    changes = reconciler.reconcile(
        {"PIXEL_8": "FASTBOOT"},
        apply=False,
    )

    assert changes == [
        {
            "serial": "PIXEL_8",
            "previous_state": DeviceState.ADB,
            "state": DeviceState.FASTBOOT,
        }
    ]
    assert registry.get("device:PIXEL_8").state is DeviceState.ADB
