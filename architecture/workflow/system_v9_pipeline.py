import asyncio
from architecture.core.routed_bus import RoutedBus

system = RoutedBus()

async def handler(event):
    print("[PIPELINE]", event)

async def main():
    system.subscribe("DEVICE_DETECTED", handler)

    # correct publish usage (NOT system.bus)
    for i in range(20):
        await system.publish("DEVICE_DETECTED", {
            "id": f"pixel-{i%3}"
        })

    await asyncio.sleep(2)

asyncio.run(main())
