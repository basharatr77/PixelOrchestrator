from queue import Queue
import json

class ControlBus:
    def __init__(self):
        self.queue = Queue()
        self.handlers = []
        self.ws_clients = set()

    def publish(self, event):
        self.queue.put(event)

    def register_ws(self, ws):
        self.ws_clients.add(ws)

    def unregister_ws(self, ws):
        self.ws_clients.discard(ws)

    def broadcast(self, event):
        dead = []
        for ws in self.ws_clients:
            try:
                ws.send(json.dumps(event))
            except:
                dead.append(ws)

        for d in dead:
            self.ws_clients.discard(d)

    def run(self):
        print("🚀 CONTROL CENTER RUNNING (STABLE v2)")
        while True:
            event = self.queue.get()
            print("EVENT:", event)
            self.broadcast(event)
