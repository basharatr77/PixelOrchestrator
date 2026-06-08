import asyncio
from fastapi import FastAPI, WebSocket
import uvicorn

from core.event_store import EventStore

app = FastAPI()
store = EventStore()

clients = set()
last_index = 0

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)

    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"ACK: {msg}")

    except:
        clients.remove(websocket)


async def event_stream():

    global last_index

    while True:
        events = store.get_events()
        new_events = events[last_index:]

        for event in new_events:
            _, etype, payload, ts = event
            msg = f"{etype} → {payload}"

            dead = set()

            for c in clients:
                try:
                    await c.send_text(msg)
                except:
                    dead.add(c)

            clients.difference_update(dead)

        last_index = len(events)
        await asyncio.sleep(1)


@app.on_event("startup")
async def startup():
    asyncio.create_task(event_stream())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
