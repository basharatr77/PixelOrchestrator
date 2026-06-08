import asyncio
from architecture.core.intelligent_control_broker import IntelligentControlBroker

broker = IntelligentControlBroker()

async def handler(event):
    print("\nPROCESSING:", event)

async def main():
    broker.subscribe("group-1", "c1", handler)
    broker.subscribe("group-1", "c2", handler)

    asyncio.create_task(broker.start())

    for i in range(6):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i%2}"}
        })

    await asyncio.sleep(2)

asyncio.run(main())
