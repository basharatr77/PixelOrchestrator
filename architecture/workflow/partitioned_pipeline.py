import asyncio
from architecture.core.partitioned_broker import PartitionedBroker

broker = PartitionedBroker(partitions=3)

async def handler(event):
    print("\nEVENT:", event)

async def main():
    broker.subscribe("DEVICE_DETECTED", handler)

    asyncio.create_task(broker.start())

    for i in range(5):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i%2}"}
        })

    await asyncio.sleep(2)

asyncio.run(main())
