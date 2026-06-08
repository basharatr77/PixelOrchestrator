import time
import random
import json
import asyncio
import threading
from datetime import datetime
from collections import deque

import websockets

from app.agents.orchestrator.ai_engine import decide
from app.agents.orchestrator.task_queue import TaskQueue


# =========================
# 💾 PERSISTENCE LAYER
# =========================
EVENT_LOG = "event_log.jsonl"


def save_event(event):
    with open(EVENT_LOG, "a") as f:
        f.write(json.dumps(event) + "\n")


def load_events():
    try:
        with open(EVENT_LOG, "r") as f:
            return [json.loads(line) for line in f.readlines()]
    except:
        return []


# =========================
# 📡 EVENT BUS (REAL TIME)
# =========================
class EventBus:
    def __init__(self):
        self.subscribers = set()
        self.queue = deque()

    def publish(self, event):
        event["timestamp"] = datetime.utcnow().isoformat()

        print("📡 EVENT:", event)

        self.queue.append(event)
        save_event(event)

        # push to websocket clients
        for ws in list(self.subscribers):
            asyncio.run_coroutine_threadsafe(
                ws.send(json.dumps(event)),
                loop
            )

    def subscribe(self, ws):
        self.subscribers.add(ws)

    def unsubscribe(self, ws):
        self.subscribers.discard(ws)


bus = EventBus()
queue = TaskQueue()


# =========================
# 🧪 FAKE DEVICE STREAM
# =========================
BASE_DEVICES = [
    {"serial": "PIXEL_7_PRO", "mode": "ADB"},
    {"serial": "SAMSUNG_A52", "mode": "ADB"},
    {"serial": "FASTBOOT_ONEPLUS", "mode": "FASTBOOT"},
]


def simulate_device_stream():
    devices = []

    for d in BASE_DEVICES:
        if random.random() > 0.3:
            device = d.copy()

            if random.random() > 0.8:
                device["mode"] = random.choice(["ADB", "FASTBOOT"])

            devices.append(device)

    if random.random() > 0.7:
        devices.append({
            "serial": f"DEV_{random.randint(10000,99999)}",
            "mode": random.choice(["ADB", "FASTBOOT"])
        })

    return devices


# =========================
# ⚡ ORCHESTRATION LOOP
# =========================
def engine_loop():
    print("🚀 Engine Running (Event Driven Mode)")

    while True:
        devices = simulate_device_stream()

        for d in devices:
            event = {"type": "DEVICE_DETECTED", "data": d}
            bus.publish(event)

            decision = decide(d)
            queue.add_task(decision)

        task = queue.pop_task()
        if task:
            print("⚡ EXECUTING:", task)

        time.sleep(3)


# =========================
# 🌐 WEBSOCKET SERVER
# =========================
async def handler(ws):
    bus.subscribe(ws)

    # send replay on connect
    history = load_events()
    for event in history[-20:]:
        await ws.send(json.dumps(event))

    try:
        async for _ in ws:
            pass
    finally:
        bus.unsubscribe(ws)


async def ws_server():
    global loop
    loop = asyncio.get_running_loop()

    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("🌐 WebSocket Server running on ws://0.0.0.0:8765")

    await server.wait_closed()


# =========================
# 🚀 MAIN ENTRY
# =========================
def main():
    t1 = threading.Thread(target=engine_loop, daemon=True)
    t1.start()

    asyncio.run(ws_server())


if __name__ == "__main__":
    main()
