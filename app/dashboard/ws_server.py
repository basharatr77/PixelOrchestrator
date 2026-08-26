import asyncio
import json

import websockets

from app.core.broadcaster import broadcaster
from app.core.event_log import EventLog
from app.core.events import Event


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


def create_handler(bus):
    async def handler(ws):
        await broadcaster.register(ws)

        try:
            async for msg in ws:
                data = json.loads(msg)

                if data.get("type") == "dashboard_connect":
                    last_offset = int(
                        data.get("last_offset", 0)
                    )

                    await replay_dashboard(
                        ws,
                        last_offset,
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
            pass

        finally:
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
