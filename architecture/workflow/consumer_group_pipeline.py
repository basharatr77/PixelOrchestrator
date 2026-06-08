import asyncio
from architecture.core.consumer_group_broker import ConsumerGroupBroker

broker = ConsumerGroupBroker(partitions=3)

async def handler(event):
    print("\nPROCESS:", event)

async def main():
    broker.subscribe("group-1", "c1", "DEVICE_DETECTED", handler)
    broker.subscribe("group-1", "c2", "DEVICE_DETECTED", handler)

    asyncio.create_task(broker.start())

    for i in range(6):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i}"}
        })

    await asyncio.sleep(2)

asyncio.run(main())
