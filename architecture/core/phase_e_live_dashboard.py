import asyncio
import json
import time
from architecture.core.control_plane import ControlPlane
import websockets

class LiveDashboard:
    def __init__(self):
        self.cp = ControlPlane()
        self.clients = set()

    async def ws_handler(self, websocket):
        self.clients.add(websocket)
        try:
            while True:
                await asyncio.sleep(1)

                metrics = self.cp.health()
                events = self.cp.get_event_bus().replay(20)

                payload = {
                    "ts": int(time.time()),
                    "metrics": metrics,
                    "events": len(events)
                }

                await websocket.send(json.dumps(payload))
        except:
            pass
        finally:
            self.clients.remove(websocket)

    async def start_ws(self):
        server = await websockets.serve(self.ws_handler, "0.0.0.0", 8765, process_request=self.process_request)self.ws_handler, "0.0.0.0", 8765)
        print("[WS] LIVE DASHBOARD ws://0.0.0.0:8765")
        await server.wait_closed()

    async def event_generator(self):
        while True:
            await self.cp.get_event_bus().publish(
                "HEARTBEAT",
                {"alive": True, "ts": int(time.time())}
            )
            await asyncio.sleep(2)

    async def start(self):
        await self.cp.start()
        asyncio.create_task(self.start_ws())
        asyncio.create_task(self.event_generator())

        while True:
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(LiveDashboard().start())
