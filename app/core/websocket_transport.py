import asyncio
import json
import threading
import uuid
import websockets

from app.core.transport import Transport


class WebSocketTransport(Transport):
    """Synchronous Transport facade over an async WebSocket connection."""

    def __init__(self, uri, serial=None, mode=None, timeout=10):
        if not isinstance(uri, str) or not uri.strip():
            raise ValueError("uri is required")

        if serial is not None and (
            not isinstance(serial, str) or not serial.strip()
        ):
            raise ValueError("serial must be a non-empty string")

        if mode is not None and (
            not isinstance(mode, str) or not mode.strip()
        ):
            raise ValueError("mode must be a non-empty string")

        self.uri = uri
        self.serial = serial
        self.mode = mode.upper() if mode else None
        self.timeout = timeout

        self._loop = None
        self._thread = None
        self._thread_ready = threading.Event()
        self._websocket = None
        self._agent_id = str(uuid.uuid4())
        self._registered = False
        self._request_lock = threading.Lock()

    def _ensure_loop(self):
        if self._thread is not None and self._thread.is_alive():
            return

        self._thread_ready.clear()

        def runner():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._thread_ready.set()
            self._loop.run_forever()

        self._thread = threading.Thread(
            target=runner,
            name="pixelorchestrator-ws-transport",
            daemon=True,
        )
        self._thread.start()

        if not self._thread_ready.wait(self.timeout):
            raise TimeoutError("WebSocket event loop failed to start.")

    def _run(self, coroutine):
        self._ensure_loop()

        future = asyncio.run_coroutine_threadsafe(
            coroutine,
            self._loop,
        )

        return future.result(timeout=self.timeout)

    async def _connect(self):
        import websockets

        if self._websocket is None:
            self._websocket = await websockets.connect(
                self.uri,
                open_timeout=self.timeout,
            )
            self._registered = False

        await self._register_agent()

        return True

    async def _disconnect(self):
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None

        self._registered = False

        return True

    async def _register_agent(self):
        if self._registered:
            return True

        request = {
            "type": "agent_register",
            "agent_id": self._agent_id,
        }

        try:
            await self._websocket.send(json.dumps(request))

            response = await asyncio.wait_for(
                self._websocket.recv(),
                timeout=self.timeout,
            )
        except websockets.exceptions.ConnectionClosed:
            self._websocket = None
            self._registered = False
            raise

        data = json.loads(response)

        if not isinstance(data, dict):
            raise ValueError("Invalid WebSocket agent registration response.")

        if data.get("success") is not True:
            raise RuntimeError(
                data.get("error", "WebSocket agent registration failed.")
            )

        if data.get("type") != "agent_register_response":
            raise ValueError("Invalid WebSocket agent registration response.")

        if data.get("agent_id") != self._agent_id:
            raise ValueError("WebSocket agent registration identity mismatch.")

        self._registered = True
        return True

    async def _request(self, operation, command=None):
        await self._connect()

        request = {
            "type": "transport_request",
            "request_id": str(uuid.uuid4()),
            "operation": operation,
        }

        if self.serial is not None:
            request["serial"] = self.serial

        if self.mode is not None:
            request["mode"] = self.mode

        if command is not None:
            request["command"] = command

        try:
            await self._websocket.send(json.dumps(request))

            response = await asyncio.wait_for(
                self._websocket.recv(),
                timeout=self.timeout,
            )
        except websockets.exceptions.ConnectionClosed:
            self._websocket = None
            self._registered = False
            raise

        data = json.loads(response)

        if not isinstance(data, dict):
            raise ValueError("Invalid WebSocket transport response.")

        if data.get("success") is False:
            raise RuntimeError(
                data.get("error", "WebSocket transport request failed.")
            )

        if "result" in data:
            return data["result"]

        return data

    def connect(self):
        return self._run(self._connect())

    def disconnect(self):
        if self._loop is None:
            return True

        loop = self._loop
        thread = self._thread

        result = self._run(self._disconnect())

        loop.call_soon_threadsafe(loop.stop)

        if thread is not threading.current_thread():
            thread.join(self.timeout)

        if thread.is_alive():
            raise TimeoutError("WebSocket event loop failed to stop.")

        self._loop = None
        self._thread = None
        self._thread_ready.clear()

        return result

    def is_connected(self):
        return self._websocket is not None

    def execute(self, command):
        if self.mode == "ADB":
            if not isinstance(command, str) or not command.strip():
                raise ValueError(
                    "ADB command must be a non-empty string"
                )

        elif self.mode == "FASTBOOT":
            if not isinstance(command, list) or not command:
                raise ValueError(
                    "FASTBOOT command must be a non-empty list"
                )

            if any(
                not isinstance(item, str) or not item.strip()
                for item in command
            ):
                raise ValueError(
                    "FASTBOOT command must contain non-empty strings"
                )

        with self._request_lock:
            return self._run(
                self._request(
                    "execute",
                    command=command,
                )
            )

    def get_device_info(self):
        with self._request_lock:
            return self._run(
                self._request(
                    "get_device_info",
                )
            )
