import asyncio
import json
import websockets
from architecture.core.control_plane import ControlPlane

class WSDashboard:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()

        self.control = ControlPlane()
        self.event_bus = self.control.get_event_bus()

    # -------------------------
    # BROADCAST
    # -------------------------
    async def broadcast(self, message):
        if not self.clients:
            return

        data = json.dumps(message)

        await asyncio.gather(*[
            client.send(data)
            for client in self.clients
        ], return_exceptions=True)

    # -------------------------
    # EVENT HOOK (REAL FIX)
    # -------------------------
    def bind_events(self):
        # wrap publish function instead of wildcard
        original_publish = self.event_bus.publish

        async def hooked_publish(event_type, data):
            await original_publish(event_type, data)

            await self.broadcast({
                "type": event_type,
                "data": data
            })

        self.event_bus.publish = hooked_publish

    # -------------------------
    # CLIENT HANDLER
    # -------------------------
    async def handler(self, websocket):
        self.clients.add(websocket)

        try:
            async for _ in websocket:
                pass
        finally:
            self.clients.remove(websocket)

    # -------------------------
    # START SERVER
    # -------------------------
    async def start(self):
        await self.control.start()

        self.bind_events()

        server = await websockets.serve(
            self.handler,
            self.host,
            self.port
        )

        print(f"[WS] REAL Dashboard running on ws://{self.host}:{self.port}")
        await server.wait_closed()
