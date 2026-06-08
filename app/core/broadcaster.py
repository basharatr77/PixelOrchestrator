import asyncio
import json

class Broadcaster:
    def __init__(self):
        self.clients = set()

    async def register(self, ws):
        self.clients.add(ws)
        print("Client connected:", len(self.clients))

    async def unregister(self, ws):
        self.clients.remove(ws)
        print("Client disconnected:", len(self.clients))

    async def broadcast(self, message):
        if self.clients:
            data = json.dumps(message)
            await asyncio.gather(
                *[client.send(data) for client in self.clients],
                return_exceptions=True
            )

broadcaster = Broadcaster()
