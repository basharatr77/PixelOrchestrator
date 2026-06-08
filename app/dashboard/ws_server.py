import asyncio
import websockets
import json
from app.core.broadcaster import broadcaster
from app.core.event_bus import EventBus

bus = EventBus()

# Bridge EventBus → WebSocket Broadcast
def push_to_ws(event):
    asyncio.create_task(broadcaster.broadcast(event))

bus.subscribe("DEVICE_CONNECTED", push_to_ws)
bus.subscribe("EVENT", push_to_ws)

async def handler(ws):
    await broadcaster.register(ws)

    try:
        async for msg in ws:
            data = json.loads(msg)

            # Inject back into EventBus (2-way system)
            bus.publish(data)

    except:
        pass
    finally:
        await broadcaster.unregister(ws)

async def main():
    print("🚀 Real-Time Broadcast Server :8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

asyncio.run(main())
