import asyncio
import json

import websockets

from app.logger import logger

from app.core.adb_transport import ADBTransport
from app.core.agent_registry import Agent, AgentRegistry
from app.core.broadcaster import broadcaster
from app.core.event_log import EventLog
from app.core.events import Event
from app.core.fastboot_transport import FastbootTransport


DASHBOARD_GROUP = "dashboard"

DASHBOARD_EVENT_TYPES = (
    "DEVICE_CONNECTED",
    "DEVICE_MODE_CHANGED",
    "DEVICE_DISCONNECTED",
    "TASK_EXECUTED",
)


def _event_to_dict(event, offset=None):
    data = {
        "id": event.id,
        "type": event.type,
        "ts": event.ts,
        "payload": event.payload,
    }

    if offset is not None:
        data["offset"] = offset

    return data


def push_to_ws(event, offset, group_id):
    asyncio.create_task(
        broadcaster.broadcast(
            _event_to_dict(event, offset)
        )
    )


def subscribe_dashboard(bus):
    for event_type in DASHBOARD_EVENT_TYPES:
        bus.subscribe(
            DASHBOARD_GROUP,
            event_type,
            push_to_ws,
        )


async def replay_dashboard(ws, last_offset):
    log = EventLog()

    for item in log.read_from(last_offset):
        if item["type"] not in DASHBOARD_EVENT_TYPES:
            continue

        await ws.send(json.dumps(item))


def _transport_for_request(data):
    serial = data.get("serial")
    mode = data.get("mode")

    if not isinstance(serial, str) or not serial.strip():
        raise ValueError("serial is required")

    if not isinstance(mode, str) or not mode.strip():
        raise ValueError("mode is required")

    mode = mode.upper()

    if mode == "ADB":
        return ADBTransport(serial)

    if mode == "FASTBOOT":
        return FastbootTransport(serial)

    raise ValueError(f"Unsupported transport mode: {mode}")


def execute_transport_request(data, device_registry=None, ownership=None, agent_id=None):
    request_id = data.get("request_id")

    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id is required")

    operation = data.get("operation")

    if operation not in {
        "execute",
        "get_device_info",
    }:
        raise ValueError(
            f"Unsupported transport operation: {operation}"
        )

    serial = data.get("serial")
    device_id = f"device:{serial}" if isinstance(serial, str) else None

    if ownership is not None:
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent identity required for device ownership")

        if not isinstance(serial, str) or not serial.strip():
            raise ValueError("serial is required for device ownership")

        if not ownership.owns(agent_id, device_id):
            logger.warning(
                "Remote agent device ownership rejected: %s -> %s",
                agent_id,
                device_id,
                extra={
                    "event": "device_ownership_rejected",
                    "agent_id": agent_id,
                    "request_id": request_id,
                },
            )
            raise PermissionError(
                f"Agent '{agent_id}' does not have ownership of device '{device_id}'."
            )

        if device_registry is not None and not device_registry.contains(device_id):
            raise ValueError(
                f"Device '{device_id}' is not registered."
            )

    mode = data.get("mode").upper()

    if operation == "get_device_info" and device_registry is not None:
        device = device_registry.get(device_id)
        if device is not None:
            return {
                "type": "transport_response",
                "request_id": request_id,
                "success": True,
                "result": {
                    "device_id": device.device_id,
                    "serial": device.serial,
                    "model": device.model,
                    "state": device.state.value,
                    "transport": device.transport,
                    "properties": dict(device.properties),
                    "capabilities": list(device.capabilities or ()),
                },
            }

    transport = _transport_for_request(data)

    if operation == "execute":
        command = data.get("command")

        if mode == "ADB":
            if not isinstance(command, str) or not command.strip():
                raise ValueError(
                    "ADB command must be a non-empty string"
                )

        elif mode == "FASTBOOT":
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

        result = transport.execute(command)

    else:
        result = transport.get_device_info()

    return {
        "type": "transport_response",
        "request_id": request_id,
        "success": True,
        "result": result,
    }


async def handle_transport_request(ws, data, device_registry=None, ownership=None, agent_id=None):
    try:
        response = await asyncio.to_thread(
            execute_transport_request,
            data,
            device_registry,
            ownership,
            agent_id,
        )
    except (ValueError, PermissionError) as exc:
        response = {
            "type": "transport_response",
            "request_id": data.get("request_id"),
            "success": False,
            "error": str(exc),
        }
    except Exception:
        logger.exception(
            "Unexpected transport request failure",
            extra={
                "event": "transport_request_failed",
                "agent_id": agent_id,
                "request_id": data.get("request_id"),
            },
        )
        response = {
            "type": "transport_response",
            "request_id": data.get("request_id"),
            "success": False,
            "error": "transport request failed",
        }

    await ws.send(json.dumps(response))


def create_handler(bus, agent_registry=None, device_registry=None, ownership=None, authenticator=None):
    if agent_registry is None:
        agent_registry = AgentRegistry()
    async def handler(ws):
        await broadcaster.register(ws)
        registered_agent_id = None
        connection_id = str(id(ws))

        try:
            async for msg in ws:
                try:
                    data = json.loads(msg)
                except (json.JSONDecodeError, TypeError):
                    continue

                if not isinstance(data, dict):
                    continue

                if data.get("type") == "agent_register":
                    agent_id = data.get("agent_id")

                    if registered_agent_id is not None:
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "agent_register_response",
                                    "success": False,
                                    "error": "agent already registered",
                                }
                            )
                        )
                        continue

                    if not isinstance(agent_id, str) or not agent_id.strip():
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "agent_register_response",
                                    "success": False,
                                    "error": "agent_id is required",
                                }
                            )
                        )
                        continue

                    if authenticator is None:
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "agent_register_response",
                                    "success": False,
                                    "error": "authentication required",
                                }
                            )
                        )
                        continue

                    try:
                        authenticated = authenticator.authenticate(
                            agent_id,
                            data,
                        )
                    except Exception:
                        authenticated = False

                    if authenticated is not True:
                        logger.warning(
                            "Remote agent authentication failed: %s",
                            agent_id,
                            extra={
                                "event": "agent_authentication_failed",
                                "agent_id": agent_id,
                            },
                        )
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "agent_register_response",
                                    "success": False,
                                    "error": "authentication failed",
                                }
                            )
                        )
                        continue

                    if agent_registry.get(agent_id) is None:
                        logger.warning(
                            "Remote agent authorization rejected: %s",
                            agent_id,
                            extra={
                                "event": "agent_authorization_rejected",
                                "agent_id": agent_id,
                            },
                        )
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "agent_register_response",
                                    "success": False,
                                    "error": "agent not authorized",
                                }
                            )
                        )
                        continue

                    agent_registry.claim_connection(agent_id, connection_id)
                    registered_agent_id = agent_id

                    await ws.send(
                        json.dumps(
                            {
                                "type": "agent_register_response",
                                "success": True,
                                "agent_id": registered_agent_id,
                            }
                        )
                    )

                    continue

                if data.get("type") == "dashboard_connect":
                    last_offset = int(
                        data.get("last_offset", 0)
                    )

                    await replay_dashboard(
                        ws,
                        last_offset,
                    )

                    continue

                if data.get("type") == "transport_request":
                    if registered_agent_id is None:
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "transport_response",
                                    "request_id": data.get("request_id"),
                                    "success": False,
                                    "error": "agent registration required",
                                }
                            )
                        )
                        continue

                    if not agent_registry.is_connection_current(
                        registered_agent_id,
                        connection_id,
                    ):
                        logger.warning(
                            "Remote agent connection rejected as stale: %s",
                            registered_agent_id,
                        )
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "transport_response",
                                    "request_id": data.get("request_id"),
                                    "success": False,
                                    "error": "agent connection is no longer current",
                                }
                            )
                        )
                        continue
                    await handle_transport_request(
                        ws,
                        data,
                        device_registry=device_registry,
                        ownership=ownership,
                        agent_id=registered_agent_id,
                    )

                    continue

                event_type = data.get("type")

                if not event_type:
                    continue

                event = Event(
                    type=event_type,
                    payload=data.get("payload", {}),
                )

                await bus.publish(event)

        except Exception:
            logger.exception("Unexpected dashboard WebSocket handler failure")

        finally:
            if registered_agent_id is not None:
                try:
                    agent_registry.release_connection(
                        registered_agent_id,
                        connection_id,
                    )
                except KeyError:
                    pass
            await broadcaster.unregister(ws)

    return handler


async def run_dashboard(bus):
    subscribe_dashboard(bus)

    handler = create_handler(bus)

    print("?? Dashboard WebSocket Server :8765")

    async with websockets.serve(
        handler,
        "0.0.0.0",
        8765,
    ):
        await asyncio.Future()
