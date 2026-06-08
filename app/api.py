import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue
from database import init_db, add_device

class EventBus:
    def __init__(self):
        self.queue = Queue()
        self.handlers = {}

    def subscribe(self, event_type, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    def publish(self, event):
        self.queue.put(event)

    def worker(self):
        print("EventBus running 🚀")
        while True:
            event = self.queue.get()
            etype = event.get("type")
            print("EVENT:", event)
            if etype in self.handlers:
                for h in self.handlers[etype]:
                    h(event)

bus = EventBus()

def device_handler(event):
    device = event.get("payload")
    print("DEVICE:", device)
    add_device(device, "connected")

bus.subscribe("DEVICE_CONNECTED", device_handler)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"status":"PixelOrchestrator running"}).encode())

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(length))
        bus.publish(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"message":"event queued"}).encode())

init_db()
threading.Thread(target=bus.worker, daemon=True).start()

print("Server starting on port 8000...")
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
