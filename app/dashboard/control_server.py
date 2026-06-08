import asyncio
import websockets
import json
import socket

from app.core.control_bus import ControlBus

def free_port(port):
    s = socket.socket()
    try:
        s.bind(("0.0.0.0", port))
        s.close()
        return True
    except:
        return False

PORT = 8780
if not free_port(PORT):
    print("⚠️ Port busy, switching to 8766")
    PORT = 8766

bus = ControlBus()

async def handler(ws):
    bus.register_ws(ws)

    try:
        async for msg in ws:
            bus.publish(json.loads(msg))
    finally:
        bus.unregister_ws(ws)

async def main():
    print(f"🚀 CONTROL CENTER RUNNING ON {PORT}")

    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    import threading
    threading.Thread(target=bus.run, daemon=True).start()
    asyncio.run(main())
