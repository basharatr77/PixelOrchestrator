import json


class WebSocketBridge:
    def __init__(self):
        self.clients = set()

    def register(self, ws):
        self.clients.add(ws)

    def unregister(self, ws):
        self.clients.discard(ws)

    async def broadcast(self, event):
        dead = []

        for ws in self.clients:
            try:
                await ws.send(json.dumps(event.to_dict()))
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.clients.discard(ws)
