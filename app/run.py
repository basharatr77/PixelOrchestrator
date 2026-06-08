import asyncio
from app.core.events import Event
from app.core.bus_runtime import BusRuntime


async def main():
    runtime = BusRuntime()

    await runtime.bus.publish(Event(
        type="device_connected",
        payload={"id": "pixel-1"}
    ))

    await runtime.bus.publish(Event(
        type="device_connected",
        payload={"id": "pixel-2"}
    ))

    await runtime.run()


if __name__ == "__main__":
    asyncio.run(main())
