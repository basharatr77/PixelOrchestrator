import pytest

from app.core.module_contract import (
    Action,
    Capability,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)


def make_manifest(**kwargs):
    defaults = {
        "id": "test",
        "name": "Test",
        "version": "1.0.0",
        "module_type": ModuleType.COMMON,
    }
    defaults.update(kwargs)
    return ModuleManifest(**defaults)


def validate(manifest):
    type(
        "TestModule",
        (ModuleContract,),
        {"manifest": manifest},
    )().validate_manifest()


def test_empty_module_id_is_rejected():
    with pytest.raises(ValueError, match="Module manifest ID cannot be empty"):
        validate(make_manifest(id=""))


def test_empty_capability_id_is_rejected():
    with pytest.raises(ValueError, match="Capability ID cannot be empty"):
        validate(
            make_manifest(
                capabilities=(
                    Capability(id="", name="Broken"),
                )
            )
        )


def test_empty_action_id_is_rejected():
    with pytest.raises(ValueError, match="Action ID cannot be empty"):
        validate(
            make_manifest(
                actions=(
                    Action(id="", name="Broken"),
                )
            )
        )


def test_empty_capability_reference_is_rejected():
    with pytest.raises(
        ValueError,
        match="Action capability ID cannot be empty when provided",
    ):
        validate(
            make_manifest(
                actions=(
                    Action(
                        id="test_action",
                        name="Test",
                        capability_id="   ",
                    ),
                )
            )
        )


def test_duplicate_capability_ids_are_rejected():
    with pytest.raises(
        ValueError,
        match="Duplicate capability ID: same",
    ):
        validate(
            make_manifest(
                capabilities=(
                    Capability(id="same", name="One"),
                    Capability(id="same", name="Two"),
                )
            )
        )


def test_duplicate_action_ids_are_rejected():
    with pytest.raises(
        ValueError,
        match="Duplicate action ID: same",
    ):
        validate(
            make_manifest(
                actions=(
                    Action(id="same", name="One"),
                    Action(id="same", name="Two"),
                )
            )
        )


def test_unknown_capability_reference_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unknown capability ID: missing",
    ):
        validate(
            make_manifest(
                capabilities=(
                    Capability(id="real", name="Real"),
                ),
                actions=(
                    Action(
                        id="test_action",
                        name="Test",
                        capability_id="missing",
                    ),
                ),
            )
        )
