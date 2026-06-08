import asyncio
from architecture.core.control_broker import ControlBroker

broker = ControlBroker()

async def handler(event):
    print("\nEVENT:", event)

async def main():
    broker.subscribe("group-1", "c1", handler)
    broker.subscribe("group-1", "c2", handler)

    asyncio.create_task(broker.start())

    for i in range(5):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i}"}
        })

    await asyncio.sleep(2)

asyncio.run(main())
