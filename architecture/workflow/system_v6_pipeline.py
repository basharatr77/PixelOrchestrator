import asyncio
from architecture.core.event_system_v6 import EventSystemV6

system = EventSystemV6()

async def handler(event):
    print("[PROCESS]", event)

async def main():
    system.subscribe("group-1", handler)
    system.subscribe("group-2", handler)

    asyncio.create_task(system.start())

    for i in range(20):
        system.publish("DEVICE_DETECTED", {
            "id": f"pixel-{i%3}"
        })

    await asyncio.sleep(3)

asyncio.run(main())
