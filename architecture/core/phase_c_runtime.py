import asyncio
import time
import json
from collections import defaultdict, deque

# ---------------------------
# EVENT CORE (enhanced)
# ---------------------------
class EventHub:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.subscribers = defaultdict(list)
        self.log = deque(maxlen=5000)
        self.running = False

    async def publish(self, event_type, data):
        event = {
            "type": event_type,
            "data": data,
            "ts": int(time.time())
        }

        self.log.append(event)
        await self.queue.put(event)

        for cb in self.subscribers[event_type]:
            cb(event)

    def subscribe(self, event_type, cb):
        self.subscribers[event_type].append(cb)

    async def worker(self):
        while self.running:
            event = await self.queue.get()
            print(f"[STREAM] {event}")

    async def start(self):
        self.running = True
        asyncio.create_task(self.worker())
        print("[EVENT_HUB] RUNNING")

    def replay(self, limit=20):
        return list(self.log)[-limit:]


# ---------------------------
# METRICS ENGINE
# ---------------------------
class MetricsEngine:
    def __init__(self, hub):
        self.hub = hub
        self.count = 0
        self.start_time = time.time()

    def bind(self):
        def counter(event):
            self.count += 1

        self.hub.subscribe("DEVICE_DETECTED", counter)
        self.hub.subscribe("HEARTBEAT", counter)

    def snapshot(self):
        duration = max(time.time() - self.start_time, 1)
        return {
            "events": self.count,
            "events_per_sec": round(self.count / duration, 2)
        }


# ---------------------------
# WEBSOCKET DASHBOARD
# ---------------------------
class WSDashboard:
    def __init__(self, hub, metrics):
        self.hub = hub
        self.metrics = metrics
        self.clients = set()

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            while True:
                await asyncio.sleep(1)
                data = {
                    "metrics": self.metrics.snapshot(),
                    "latest": list(self.hub.log)[-5:]
                }
                await websocket.send(json.dumps(data))
        except:
            pass
        finally:
            self.clients.remove(websocket)

    async def start(self):
        import websockets

        self.server = await websockets.serve(self.handler, "0.0.0.0", 8765)
        print("[WS] DASHBOARD RUNNING ws://0.0.0.0:8765")
        await self.server.wait_closed()


# ---------------------------
# CONTROL PLANE
# ---------------------------
class ControlPlane:
    def __init__(self):
        self.hub = EventHub()
        self.metrics = MetricsEngine(self.hub)
        self.dashboard = WSDashboard(self.hub, self.metrics)

    async def start(self):
        await self.hub.start()
        self.metrics.bind()
        print("[CONTROL] STARTED")

        asyncio.create_task(self.dashboard.start())

    async def emit(self, event_type, data):
        await self.hub.publish(event_type, data)

    def replay(self):
        return self.hub.replay()


# ---------------------------
# BOOT STRAP TEST
# ---------------------------
async def main():
    cp = ControlPlane()
    await cp.start()

    # demo events
    while True:
        await cp.emit("HEARTBEAT", {"alive": True})
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
