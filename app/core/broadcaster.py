import asyncio
import json


class Broadcaster:
    def __init__(self):
        # Existing connections: agents and other general-purpose clients.
        self.clients = set()

        # Separate connections for dashboard clients.
        self.dashboard_clients = set()

    async def register(self, ws):
        self.clients.add(ws)
        print("Client connected:", len(self.clients))

    async def unregister(self, ws):
        self.clients.discard(ws)
        print("Client disconnected:", len(self.clients))

    async def register_dashboard(self, ws):
        self.dashboard_clients.add(ws)

    async def unregister_dashboard(self, ws):
        self.dashboard_clients.discard(ws)

    async def broadcast(self, message):
        """Broadcast using the existing general-purpose client group."""
        if self.clients:
            data = json.dumps(message)

            await asyncio.gather(
                *[
                    client.send(data)
                    for client in self.clients
                ],
                return_exceptions=True,
            )

    async def broadcast_dashboard(self, message):
        """Broadcast dashboard events only to dashboard clients."""
        if self.dashboard_clients:
            data = json.dumps(message)

            await asyncio.gather(
                *[
                    client.send(data)
                    for client in self.dashboard_clients
                ],
                return_exceptions=True,
            )


broadcaster = Broadcaster()