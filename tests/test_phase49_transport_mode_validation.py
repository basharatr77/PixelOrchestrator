import pytest

from app.dashboard.ws_server import execute_transport_request


def test_execute_transport_request_rejects_missing_mode_as_validation_error():
    with pytest.raises(ValueError, match="mode is required"):
        execute_transport_request(
            {
                "request_id": "request-missing-mode",
                "operation": "execute",
                "serial": "DEVICE-001",
            }
        )
