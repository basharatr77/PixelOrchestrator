import asyncio
import json
import time
from architecture.core.control_plane import ControlPlane

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>PixelOrchestrator Dashboard</title>
    <style>
        body { background:#0d1117; color:#00ff88; font-family:monospace; }
        #log { height:80vh; overflow:auto; border:1px solid #333; padding:10px; }
    </style>
</head>
<body>
<h2>⚡ PixelOrchestrator LIVE DASHBOARD</h2>
<div id="log"></div>

<script>
let ws = new WebSocket("ws://127.0.0.1:8765");

ws.onmessage = function(event){
    let log = document.getElementById("log");
    let data = JSON.parse(event.data);

    let div = document.createElement("div");
    div.innerText = JSON.stringify(data);
    log.appendChild(div);

    log.scrollTop = log.scrollHeight;
};
</script>
</body>
</html>
"""


class DashboardServer:
    def __init__(self):
        self.cp = ControlPlane()

    async def start_ws(self):
        import websockets

        async def handler(ws):
            while True:
                await asyncio.sleep(1)
                data = {
                    "ts": int(time.time()),
                    "metrics": self.cp.health(),
                    "events": len(self.cp.get_event_bus().replay(10))
                }
                await ws.send(json.dumps(data))

        self.server = await websockets.serve(handler, "0.0.0.0", 8765)
        print("[WS] DASHBOARD RUNNING ws://0.0.0.0:8765")
        await self.server.wait_closed()

    async def start(self):
        await self.cp.start()
        asyncio.create_task(self.start_ws())

        while True:
            await self.cp.get_event_bus().publish(
                "HEARTBEAT",
                {"alive": True}
            )
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(DashboardServer().start())
