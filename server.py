import asyncio
from fastapi import FastAPI, WebSocket
import uvicorn

from core.event_store import EventStore
from core.broadcast_queue import BroadcastQueue

app = FastAPI()

store = EventStore()
bus = BroadcastQueue()

last_index = 0


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    bus.register(websocket)

    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"ACK: {msg}")

    except:
        bus.unregister(websocket)


async def event_loop():
    global last_index

    while True:
        events = store.get_events()
        new_events = events[last_index:]

        for event in new_events:
            _, etype, payload, ts = event
            message = f"{etype} | {payload}"
            await bus.push(message)

        last_index = len(events)
        await asyncio.sleep(0.5)


@app.on_event("startup")
async def startup():
    asyncio.create_task(bus.broadcaster())
    asyncio.create_task(event_loop())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
