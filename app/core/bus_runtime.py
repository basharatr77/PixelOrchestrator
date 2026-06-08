import asyncio
from app.core.event_bus import StreamBus
from app.core.worker_pool import WorkerPool


class BusRuntime:
    def __init__(self):
        self.bus = StreamBus()
        self.pool = WorkerPool(self.bus, worker_count=3)

    def setup(self):

        def worker_a(event, offset, group):
            print(f"[A] {offset} -> {event.payload}")

        def worker_b(event, offset, group):
            print(f"[B] {offset} -> {event.payload}")

        self.bus.subscribe("group-a", "device_connected", worker_a)
        self.bus.subscribe("group-b", "device_connected", worker_b)

    async def run(self):
        self.setup()

        await self.pool.start()

        while True:
            await asyncio.sleep(3600)
