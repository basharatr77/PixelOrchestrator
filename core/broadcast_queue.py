import asyncio

class BroadcastQueue:

    def __init__(self):
        self.queue = asyncio.Queue()
        self.clients = set()

    def register(self, ws):
        self.clients.add(ws)

    def unregister(self, ws):
        self.clients.discard(ws)

    async def push(self, message):
        await self.queue.put(message)

    async def broadcaster(self):
        while True:
            msg = await self.queue.get()

            dead = set()

            for client in self.clients:
                try:
                    await client.send_text(msg)
                except:
                    dead.add(client)

            for d in dead:
                self.clients.discard(d)
