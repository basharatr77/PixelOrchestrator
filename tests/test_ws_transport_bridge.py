import asyncio
import json

from app.core.adb_transport import ADBTransport
from app.core.fastboot_transport import FastbootTransport
from app.dashboard.ws_server import (
    _transport_for_request,
    execute_transport_request,
    handle_transport_request,
)


class FakeWebSocket:
    def __init__(self):
        self.sent = []

    async def send(self, message):
        self.sent.append(json.loads(message))


class FakeBus:
    async def publish(self, event):
        return 0


def test_transport_request_requires_serial():
    try:
        _transport_for_request({
            "mode": "ADB",
        })
    except ValueError as exc:
        assert str(exc) == "serial is required"
    else:
        raise AssertionError("Expected ValueError")


def test_transport_request_requires_mode():
    try:
        _transport_for_request({
            "serial": "REMOTE-001",
        })
    except ValueError as exc:
        assert str(exc) == "mode is required"
    else:
        raise AssertionError("Expected ValueError")


def test_transport_request_selects_adb():
    transport = _transport_for_request({
        "serial": "REMOTE-001",
        "mode": "ADB",
    })

    assert isinstance(transport, ADBTransport)
    assert transport.serial == "REMOTE-001"


def test_transport_request_selects_fastboot():
    transport = _transport_for_request({
        "serial": "REMOTE-002",
        "mode": "FASTBOOT",
    })

    assert isinstance(transport, FastbootTransport)
    assert transport.serial == "REMOTE-002"


def test_transport_request_rejects_unknown_mode():
    try:
        _transport_for_request({
            "serial": "REMOTE-003",
            "mode": "UNKNOWN",
        })
    except ValueError as exc:
        assert str(exc) == "Unsupported transport mode: UNKNOWN"
    else:
        raise AssertionError("Expected ValueError")


def test_execute_transport_request_requires_request_id():
    try:
        execute_transport_request({
            "serial": "REMOTE-001",
            "mode": "ADB",
            "operation": "get_device_info",
        })
    except ValueError as exc:
        assert str(exc) == "request_id is required"
    else:
        raise AssertionError("Expected ValueError")


def test_execute_transport_request_rejects_unknown_operation():
    try:
        execute_transport_request({
            "request_id": "req-001",
            "serial": "REMOTE-001",
            "mode": "ADB",
            "operation": "unknown",
        })
    except ValueError as exc:
        assert str(exc) == "Unsupported transport operation: unknown"
    else:
        raise AssertionError("Expected ValueError")


def test_execute_transport_request_requires_command():
    try:
        execute_transport_request({
            "request_id": "req-002",
            "serial": "REMOTE-001",
            "mode": "ADB",
            "operation": "execute",
        })
    except ValueError as exc:
        assert str(exc) == "ADB command must be a non-empty string"
    else:
        raise AssertionError("Expected ValueError")


def test_execute_transport_request_adb_protocol(monkeypatch):
    calls = []

    def fake_execute(self, command):
        calls.append((self.serial, command))
        return {
            "returncode": 0,
            "stdout": "Pixel",
            "stderr": "",
        }

    monkeypatch.setattr(
        ADBTransport,
        "execute",
        fake_execute,
    )

    response = execute_transport_request({
        "request_id": "req-003",
        "serial": "REMOTE-001",
        "mode": "ADB",
        "operation": "execute",
        "command": "getprop ro.product.model",
    })

    assert response["type"] == "transport_response"
    assert response["request_id"] == "req-003"
    assert response["success"] is True
    assert response["result"]["returncode"] == 0
    assert response["result"]["stdout"] == "Pixel"
    assert calls == [
        ("REMOTE-001", "getprop ro.product.model"),
    ]


def test_execute_transport_request_get_device_info(monkeypatch):
    calls = []

    def fake_get_device_info(self):
        calls.append(self.serial)
        return {
            "serial": self.serial,
            "model": "Pixel Remote",
            "mode": "ADB",
        }

    monkeypatch.setattr(
        ADBTransport,
        "get_device_info",
        fake_get_device_info,
    )

    response = execute_transport_request({
        "request_id": "req-004",
        "serial": "REMOTE-004",
        "mode": "ADB",
        "operation": "get_device_info",
    })

    assert response["type"] == "transport_response"
    assert response["request_id"] == "req-004"
    assert response["success"] is True
    assert response["result"]["serial"] == "REMOTE-004"
    assert response["result"]["model"] == "Pixel Remote"
    assert calls == ["REMOTE-004"]


def test_handle_transport_request_success(monkeypatch):
    def fake_execute(data):
        assert data["request_id"] == "req-005"
        return {
            "type": "transport_response",
            "request_id": "req-005",
            "success": True,
            "result": {
                "returncode": 0,
                "stdout": "ok",
                "stderr": "",
            },
        }

    monkeypatch.setattr(
        "app.dashboard.ws_server.execute_transport_request",
        fake_execute,
    )

    async def scenario():
        ws = FakeWebSocket()

        await handle_transport_request(
            ws,
            {
                "request_id": "req-005",
                "serial": "REMOTE-005",
                "mode": "ADB",
                "operation": "execute",
                "command": "echo ok",
            },
        )

        assert len(ws.sent) == 1
        assert ws.sent[0]["type"] == "transport_response"
        assert ws.sent[0]["request_id"] == "req-005"
        assert ws.sent[0]["success"] is True
        assert ws.sent[0]["result"]["stdout"] == "ok"

    asyncio.run(scenario())


def test_handle_transport_request_error_response(monkeypatch):
    def fake_execute(data):
        raise ValueError("synthetic transport failure")

    monkeypatch.setattr(
        "app.dashboard.ws_server.execute_transport_request",
        fake_execute,
    )

    async def scenario():
        ws = FakeWebSocket()

        await handle_transport_request(
            ws,
            {
                "request_id": "req-006",
                "serial": "REMOTE-006",
                "mode": "ADB",
                "operation": "execute",
                "command": "echo fail",
            },
        )

        assert len(ws.sent) == 1
        assert ws.sent[0]["type"] == "transport_response"
        assert ws.sent[0]["request_id"] == "req-006"
        assert ws.sent[0]["success"] is False
        assert ws.sent[0]["error"] == "synthetic transport failure"

    asyncio.run(scenario())


def test_execute_transport_request_accepts_adb_string(monkeypatch):
    from app.dashboard import ws_server

    captured = {}

    def fake_execute(self, command):
        captured["command"] = command
        return {
            "returncode": 0,
            "stdout": "ok",
            "stderr": "",
        }

    monkeypatch.setattr(
        ws_server.ADBTransport,
        "execute",
        fake_execute,
    )

    result = ws_server.execute_transport_request({
        "type": "transport_request",
        "request_id": "req-adb-string",
        "operation": "execute",
        "serial": "ADB-001",
        "mode": "ADB",
        "command": "getprop ro.product.model",
    })

    assert result["success"] is True
    assert captured["command"] == "getprop ro.product.model"


def test_execute_transport_request_rejects_adb_list():
    from app.dashboard import ws_server

    try:
        ws_server.execute_transport_request({
            "type": "transport_request",
            "request_id": "req-adb-list",
            "operation": "execute",
            "serial": "ADB-001",
            "mode": "ADB",
            "command": ["getprop", "ro.product.model"],
        })
    except ValueError as exc:
        assert str(exc) == "ADB command must be a non-empty string"
    else:
        raise AssertionError("Expected ValueError")


def test_execute_transport_request_accepts_fastboot_list(monkeypatch):
    from app.dashboard import ws_server

    captured = {}

    def fake_execute(self, command):
        captured["command"] = command
        return {
            "returncode": 0,
            "stdout": "",
            "stderr": "finished",
        }

    monkeypatch.setattr(
        ws_server.FastbootTransport,
        "execute",
        fake_execute,
    )

    result = ws_server.execute_transport_request({
        "type": "transport_request",
        "request_id": "req-fastboot-list",
        "operation": "execute",
        "serial": "FB-001",
        "mode": "FASTBOOT",
        "command": ["getvar", "product"],
    })

    assert result["success"] is True
    assert captured["command"] == ["getvar", "product"]


def test_execute_transport_request_rejects_fastboot_string():
    from app.dashboard import ws_server

    try:
        ws_server.execute_transport_request({
            "type": "transport_request",
            "request_id": "req-fastboot-string",
            "operation": "execute",
            "serial": "FB-001",
            "mode": "FASTBOOT",
            "command": "getvar product",
        })
    except ValueError as exc:
        assert str(exc) == "FASTBOOT command must be a non-empty list"
    else:
        raise AssertionError("Expected ValueError")


def test_execute_transport_request_rejects_fastboot_invalid_items():
    from app.dashboard import ws_server

    try:
        ws_server.execute_transport_request({
            "type": "transport_request",
            "request_id": "req-fastboot-invalid",
            "operation": "execute",
            "serial": "FB-001",
            "mode": "FASTBOOT",
            "command": ["getvar", ""],
        })
    except ValueError as exc:
        assert str(exc) == (
            "FASTBOOT command must contain non-empty strings"
        )
    else:
        raise AssertionError("Expected ValueError")
