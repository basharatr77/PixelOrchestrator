"""Shared execution-time authorization checks for module actions."""

from app.core.module_contract import ActionResult, DeviceState


def validate_action_authorization(action, capabilities, device):
    """Return a rejection result, or None when the action is permitted."""

    if not getattr(action, "enabled", True):
        return ActionResult(
            success=False,
            message=f"Action disabled: {action.id}",
            error_code="ACTION_DISABLED",
        )

    if getattr(action, "capability_id", None) is not None:
        capability = next(
            (
                item for item in capabilities
                if item.id == getattr(action, "capability_id", None)
            ),
            None,
        )

        if capability is None:
            return ActionResult(
                success=False,
                message=f"Capability not found: {getattr(action, 'capability_id', None)}",
                error_code="CAPABILITY_NOT_FOUND",
            )

        if not capability.enabled:
            return ActionResult(
                success=False,
                message=f"Capability disabled: {action.capability_id}",
                error_code="CAPABILITY_DISABLED",
            )

    if getattr(action, "requires_device", True) and device is None:
        return ActionResult(
            success=False,
            message="Device required for action.",
            error_code="DEVICE_REQUIRED",
        )

    if device is not None and getattr(action, "allowed_transports", None) is not None:
        if device.transport not in action.allowed_transports:
            return ActionResult(
                success=False,
                message="Transport not allowed for action.",
                error_code="TRANSPORT_NOT_ALLOWED",
            )

    if device is not None and getattr(action, "allowed_states", None) is not None:
        if not isinstance(device.state, DeviceState):
            return ActionResult(
                success=False,
                message="Invalid device state.",
                error_code="INVALID_DEVICE_STATE",
            )

        if device.state.value not in action.allowed_states:
            return ActionResult(
                success=False,
                message="Device state not allowed for action.",
                error_code="STATE_NOT_ALLOWED",
            )

    return None
