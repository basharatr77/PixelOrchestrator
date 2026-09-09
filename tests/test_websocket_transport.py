import asyncio
import json

from app.core.websocket_transport import WebSocketTransport


class FakeWebSocket:
    def __init__(self, responses):
        self.sent = []
        self.closed = False
        self.responses = list(responses)

    async def send(self, message):
        self.sent.append(json.loads(message))

    async def recv(self):
        return self.responses.pop(0)

    async def close(self):
        self.closed = True


class FakeConnect:
    def __init__(self, websocket):
        self.websocket = websocket
        self.calls = []

    def __call__(self, uri, **kwargs):
        self.calls.append((uri, kwargs))

        async def connect():
            return self.websocket

        return connect()


def test_websocket_transport_contract():
    transport = WebSocketTransport("ws://127.0.0.1:8765")

    assert transport.uri == "ws://127.0.0.1:8765"
    assert transport.timeout == 10


def test_websocket_transport_rejects_empty_uri():
    try:
        WebSocketTransport("")
    except ValueError as exc:
        assert str(exc) == "uri is required"
    else:
        raise AssertionError("Expected ValueError")


def test_websocket_transport_execute_protocol():
    async def scenario():
        transport = WebSocketTransport(
            "ws://127.0.0.1:8765",
            timeout=2,
        )

        websocket = FakeWebSocket([
            json.dumps({
                "type": "agent_register_response",
                "success": True,
                "agent_id": transport._agent_id,
            }),
            json.dumps({
                "success": True,
                "stdout": "hello",
                "stderr": "",
                "returncode": 0,
            }),
        ])
        connector = FakeConnect(websocket)

        import websockets

        original_connect = websockets.connect
        websockets.connect = connector

        try:
            result = transport.execute("getprop ro.product.model")

            assert result["success"] is True
            assert result["stdout"] == "hello"
            assert result["returncode"] == 0

            assert len(websocket.sent) == 2

            assert websocket.sent[0]["type"] == "agent_register"
            assert websocket.sent[0]["agent_id"] == transport._agent_id

            request = websocket.sent[1]

            assert request["type"] == "transport_request"
            assert request["operation"] == "execute"
            assert request["command"] == "getprop ro.product.model"
            assert isinstance(request["request_id"], str)
            assert request["request_id"]

            transport.disconnect()
            assert websocket.closed is True
        finally:
            websockets.connect = original_connect

    asyncio.run(scenario())


def test_websocket_transport_get_device_info_protocol():
    async def scenario():
        transport = WebSocketTransport(
            "ws://127.0.0.1:8765",
            timeout=2,
        )

        websocket = FakeWebSocket([
            json.dumps({
                "type": "agent_register_response",
                "success": True,
                "agent_id": transport._agent_id,
            }),
            json.dumps({
                "serial": "REMOTE-001",
                "model": "Pixel Test",
                "mode": "ADB",
            }),
        ])
        connector = FakeConnect(websocket)

        import websockets

        original_connect = websockets.connect
        websockets.connect = connector

        try:
            result = transport.get_device_info()

            assert result["serial"] == "REMOTE-001"
            assert result["model"] == "Pixel Test"
            assert result["mode"] == "ADB"

            assert len(websocket.sent) == 2

            assert websocket.sent[0]["type"] == "agent_register"
            assert websocket.sent[0]["agent_id"] == transport._agent_id

            request = websocket.sent[1]

            assert request["type"] == "transport_request"
            assert request["operation"] == "get_device_info"
            assert isinstance(request["request_id"], str)
            assert request["request_id"]

            transport.disconnect()
            assert websocket.closed is True
        finally:
            websockets.connect = original_connect

    asyncio.run(scenario())


def test_websocket_transport_reuses_connection():
    async def scenario():
        transport = WebSocketTransport(
            "ws://127.0.0.1:8765",
            timeout=2,
        )

        websocket = FakeWebSocket([
            json.dumps({
                "type": "agent_register_response",
                "success": True,
                "agent_id": transport._agent_id,
            }),
        ])
        connector = FakeConnect(websocket)

        import websockets

        original_connect = websockets.connect
        websockets.connect = connector

        try:
            transport.connect()
            transport.connect()

            assert len(connector.calls) == 1
            assert transport.is_connected() is True

            transport.disconnect()
            assert transport.is_connected() is False
        finally:
            websockets.connect = original_connect

    asyncio.run(scenario())


def test_websocket_transport_fastboot_command_protocol():
    async def scenario():
        transport = WebSocketTransport(
            "ws://127.0.0.1:8765",
            serial="FB-001",
            mode="FASTBOOT",
            timeout=2,
        )

        websocket = FakeWebSocket([
            json.dumps({
                "type": "agent_register_response",
                "success": True,
                "agent_id": transport._agent_id,
            }),
            json.dumps({
                "success": True,
                "returncode": 0,
                "stdout": "",
                "stderr": "finished",
            }),
        ])
        connector = FakeConnect(websocket)

        import websockets

        original_connect = websockets.connect
        websockets.connect = connector

        try:
            result = transport.execute(
                ["getvar", "product"]
            )

            assert result["success"] is True
            assert len(websocket.sent) == 2

            assert websocket.sent[0]["type"] == "agent_register"
            assert websocket.sent[0]["agent_id"] == transport._agent_id

            request = websocket.sent[1]

            assert request["type"] == "transport_request"
            assert request["operation"] == "execute"
            assert request["serial"] == "FB-001"
            assert request["mode"] == "FASTBOOT"
            assert request["command"] == ["getvar", "product"]

            transport.disconnect()
        finally:
            websockets.connect = original_connect

    asyncio.run(scenario())


def test_websocket_transport_fastboot_rejects_string_command():
    transport = WebSocketTransport(
        "ws://127.0.0.1:8765",
        serial="FB-001",
        mode="FASTBOOT",
    )

    try:
        transport.execute("getvar product")
    except ValueError as exc:
        assert str(exc) == "FASTBOOT command must be a non-empty list"
    else:
        raise AssertionError("Expected ValueError")


def test_websocket_transport_fastboot_rejects_invalid_command_items():
    transport = WebSocketTransport(
        "ws://127.0.0.1:8765",
        serial="FB-001",
        mode="FASTBOOT",
    )

    try:
        transport.execute(["getvar", ""])
    except ValueError as exc:
        assert str(exc) == (
            "FASTBOOT command must contain non-empty strings"
        )
    else:
        raise AssertionError("Expected ValueError")


def test_websocket_transport_adb_rejects_list_command():
    transport = WebSocketTransport(
        "ws://127.0.0.1:8765",
        serial="ADB-001",
        mode="ADB",
    )

    try:
        transport.execute(["getprop", "ro.product.model"])
    except ValueError as exc:
        assert str(exc) == "ADB command must be a non-empty string"
    else:
        raise AssertionError("Expected ValueError")


def test_websocket_transport_real_local_server_client(monkeypatch):
    async def scenario():
        import websockets
        from app.dashboard import ws_server

        captured = {}

        def fake_execute(self, command):
            captured["serial"] = self.serial
            captured["command"] = command
            return {
                "returncode": 0,
                "stdout": "Pixel Local Integration",
                "stderr": "",
            }

        monkeypatch.setattr(
            ws_server.ADBTransport,
            "execute",
            fake_execute,
        )

        handler = ws_server.create_handler(None)

        async with websockets.serve(
            handler,
            "127.0.0.1",
            0,
        ) as server:
            port = server.sockets[0].getsockname()[1]

            transport = WebSocketTransport(
                f"ws://127.0.0.1:{port}",
                serial="LOCAL-ADB-001",
                mode="ADB",
                timeout=5,
            )

            try:
                result = await asyncio.to_thread(
                    transport.execute,
                    "getprop ro.product.model",
                )

                assert result["returncode"] == 0
                assert result["stdout"] == (
                    "Pixel Local Integration"
                )

                assert captured["serial"] == "LOCAL-ADB-001"
                assert captured["command"] == (
                    "getprop ro.product.model"
                )
            finally:
                await asyncio.to_thread(
                    transport.disconnect,
                )

    asyncio.run(scenario())


def test_websocket_transport_real_local_fastboot_server_client(monkeypatch):
    async def scenario():
        import websockets
        from app.dashboard import ws_server

        captured = {}

        def fake_execute(self, command):
            captured["serial"] = self.serial
            captured["command"] = command
            return {
                "returncode": 0,
                "stdout": "",
                "stderr": "Finished. Total time: 0.001s",
            }

        monkeypatch.setattr(
            ws_server.FastbootTransport,
            "execute",
            fake_execute,
        )

        handler = ws_server.create_handler(None)

        async with websockets.serve(
            handler,
            "127.0.0.1",
            0,
        ) as server:
            port = server.sockets[0].getsockname()[1]

            transport = WebSocketTransport(
                f"ws://127.0.0.1:{port}",
                serial="LOCAL-FASTBOOT-001",
                mode="FASTBOOT",
                timeout=5,
            )

            try:
                result = await asyncio.to_thread(
                    transport.execute,
                    ["getvar", "product"],
                )

                assert result["returncode"] == 0
                assert result["stderr"] == (
                    "Finished. Total time: 0.001s"
                )

                assert captured["serial"] == "LOCAL-FASTBOOT-001"
                assert captured["command"] == [
                    "getvar",
                    "product",
                ]
            finally:
                await asyncio.to_thread(
                    transport.disconnect,
                )

    asyncio.run(scenario())


def test_websocket_transport_real_local_adb_get_device_info(monkeypatch):
    async def scenario():
        import websockets
        from app.dashboard import ws_server

        captured = {}

        def fake_get_device_info(self):
            captured["serial"] = self.serial
            return {
                "serial": self.serial,
                "brand": "Google",
                "model": "Pixel Local ADB",
                "android_version": "16",
            }

        monkeypatch.setattr(
            ws_server.ADBTransport,
            "get_device_info",
            fake_get_device_info,
        )

        handler = ws_server.create_handler(None)

        async with websockets.serve(
            handler,
            "127.0.0.1",
            0,
        ) as server:
            port = server.sockets[0].getsockname()[1]

            transport = WebSocketTransport(
                f"ws://127.0.0.1:{port}",
                serial="LOCAL-ADB-INFO-001",
                mode="ADB",
                timeout=5,
            )

            try:
                result = await asyncio.to_thread(
                    transport.get_device_info,
                )

                assert result["serial"] == "LOCAL-ADB-INFO-001"
                assert result["brand"] == "Google"
                assert result["model"] == "Pixel Local ADB"
                assert result["android_version"] == "16"
                assert captured["serial"] == "LOCAL-ADB-INFO-001"
            finally:
                await asyncio.to_thread(
                    transport.disconnect,
                )

    asyncio.run(scenario())


def test_websocket_transport_real_local_fastboot_get_device_info(monkeypatch):
    async def scenario():
        import websockets
        from app.dashboard import ws_server

        captured = {}

        def fake_get_device_info(self):
            captured["serial"] = self.serial
            return {
                "serial": self.serial,
                "product": "Pixel Local Fastboot",
                "mode": "FASTBOOT",
            }

        monkeypatch.setattr(
            ws_server.FastbootTransport,
            "get_device_info",
            fake_get_device_info,
        )

        handler = ws_server.create_handler(None)

        async with websockets.serve(
            handler,
            "127.0.0.1",
            0,
        ) as server:
            port = server.sockets[0].getsockname()[1]

            transport = WebSocketTransport(
                f"ws://127.0.0.1:{port}",
                serial="LOCAL-FASTBOOT-INFO-001",
                mode="FASTBOOT",
                timeout=5,
            )

            try:
                result = await asyncio.to_thread(
                    transport.get_device_info,
                )

                assert result["serial"] == "LOCAL-FASTBOOT-INFO-001"
                assert result["product"] == "Pixel Local Fastboot"
                assert result["mode"] == "FASTBOOT"
                assert captured["serial"] == "LOCAL-FASTBOOT-INFO-001"
            finally:
                await asyncio.to_thread(
                    transport.disconnect,
                )

    asyncio.run(scenario())


def test_websocket_transport_real_local_server_error_to_client_exception(
    monkeypatch,
):
    async def scenario():
        import websockets
        from app.dashboard import ws_server

        def fake_execute(self, command):
            raise RuntimeError("simulated remote transport failure")

        monkeypatch.setattr(
            ws_server.ADBTransport,
            "execute",
            fake_execute,
        )

        handler = ws_server.create_handler(None)

        async with websockets.serve(
            handler,
            "127.0.0.1",
            0,
        ) as server:
            port = server.sockets[0].getsockname()[1]

            transport = WebSocketTransport(
                f"ws://127.0.0.1:{port}",
                serial="LOCAL-ADB-ERROR-001",
                mode="ADB",
                timeout=5,
            )

            try:
                try:
                    await asyncio.to_thread(
                        transport.execute,
                        "getprop ro.product.model",
                    )
                except RuntimeError as exc:
                    assert str(exc) == (
                        "simulated remote transport failure"
                    )
                else:
                    raise AssertionError(
                        "Expected RuntimeError from remote transport"
                    )
            finally:
                await asyncio.to_thread(
                    transport.disconnect,
                )

    asyncio.run(scenario())




def test_websocket_transport_marks_connection_lost_after_remote_close():
    async def scenario():
        import websockets

        async def server_handler(ws):
            async for message in ws:
                data = json.loads(message)
                if data.get("type") == "agent_register":
                    await ws.send(
                        json.dumps({
                            "type": "agent_register_response",
                            "success": True,
                            "agent_id": data["agent_id"],
                        })
                    )
                    continue
                if data.get("type") == "transport_request":
                    await ws.close()

        async with websockets.serve(
            server_handler,
            "127.0.0.1",
            0,
        ) as server:
            port = server.sockets[0].getsockname()[1]

            transport = WebSocketTransport(
                f"ws://127.0.0.1:{port}",
                serial="LOSS-CONTRACT-001",
                mode="ADB",
                timeout=2,
            )

            try:
                await asyncio.to_thread(transport.connect)

                try:
                    await asyncio.to_thread(
                        transport.execute,
                        "getprop ro.product.model",
                    )
                except Exception:
                    pass
                else:
                    raise AssertionError(
                        "Expected connection-loss exception"
                    )

                assert transport.is_connected() is False

            finally:
                if transport.is_connected():
                    await asyncio.to_thread(
                        transport.disconnect,
                    )

    asyncio.run(scenario())

def test_websocket_transport_real_local_connection_lifecycle(monkeypatch):
    async def scenario():
        import websockets
        from app.dashboard import ws_server

        connection_count = {"value": 0}

        original_connect = websockets.connect

        async def server_handler(ws):
            connection_count["value"] += 1

            async for message in ws:
                data = json.loads(message)
                if data.get("type") == "agent_register":
                    await ws.send(
                        json.dumps({
                            "type": "agent_register_response",
                            "success": True,
                            "agent_id": data["agent_id"],
                        })
                    )
                    continue

                if data.get("type") != "transport_request":
                    continue

                await ws.send(
                    json.dumps({
                        "type": "transport_response",
                        "request_id": data["request_id"],
                        "success": True,
                        "result": {
                            "returncode": 0,
                            "stdout": "lifecycle-ok",
                            "stderr": "",
                        },
                    })
                )

        async with websockets.serve(
            server_handler,
            "127.0.0.1",
            0,
        ) as server:
            port = server.sockets[0].getsockname()[1]

            transport = WebSocketTransport(
                f"ws://127.0.0.1:{port}",
                serial="LOCAL-LIFECYCLE-001",
                mode="ADB",
                timeout=5,
            )

            try:
                first = await asyncio.to_thread(
                    transport.connect,
                )

                assert first is True
                assert transport.is_connected() is True

                first_result = await asyncio.to_thread(
                    transport.execute,
                    "getprop ro.product.model",
                )

                assert first_result["stdout"] == "lifecycle-ok"
                assert connection_count["value"] == 1

                second = await asyncio.to_thread(
                    transport.connect,
                )

                assert second is True
                assert transport.is_connected() is True
                assert connection_count["value"] == 1

                second_result = await asyncio.to_thread(
                    transport.execute,
                    "getprop ro.product.model",
                )

                assert second_result["stdout"] == "lifecycle-ok"
                assert connection_count["value"] == 1

                disconnected = await asyncio.to_thread(
                    transport.disconnect,
                )

                assert disconnected is True
                assert transport.is_connected() is False

                reconnected = await asyncio.to_thread(
                    transport.connect,
                )

                assert reconnected is True
                assert transport.is_connected() is True

                third_result = await asyncio.to_thread(
                    transport.execute,
                    "getprop ro.product.model",
                )

                assert third_result["stdout"] == "lifecycle-ok"
                assert connection_count["value"] == 2
            finally:
                if transport.is_connected():
                    await asyncio.to_thread(
                        transport.disconnect,
                    )

    asyncio.run(scenario())


def test_websocket_transport_real_local_concurrent_request_response_isolation(
    monkeypatch,
):
    async def scenario():
        import websockets
        from app.dashboard import ws_server

        def fake_execute(self, command):
            return {
                "returncode": 0,
                "stdout": f"response:{command}",
                "stderr": "",
            }

        monkeypatch.setattr(
            ws_server.ADBTransport,
            "execute",
            fake_execute,
        )

        handler = ws_server.create_handler(None)

        async with websockets.serve(
            handler,
            "127.0.0.1",
            0,
        ) as server:
            port = server.sockets[0].getsockname()[1]

            transport = WebSocketTransport(
                f"ws://127.0.0.1:{port}",
                serial="LOCAL-CONCURRENT-001",
                mode="ADB",
                timeout=5,
            )

            try:
                await asyncio.to_thread(
                    transport.connect,
                )

                commands = [
                    "command-alpha",
                    "command-beta",
                    "command-gamma",
                    "command-delta",
                ]

                results = await asyncio.gather(
                    *[
                        asyncio.to_thread(
                            transport.execute,
                            command,
                        )
                        for command in commands
                    ]
                )

                assert len(results) == len(commands)

                returned = {
                    result["stdout"]
                    for result in results
                }

                expected = {
                    f"response:{command}"
                    for command in commands
                }

                assert returned == expected

                for command, result in zip(commands, results):
                    assert result["stdout"] == (
                        f"response:{command}"
                    )
                    assert result["returncode"] == 0
            finally:
                await asyncio.to_thread(
                    transport.disconnect,
                )

    asyncio.run(scenario())
