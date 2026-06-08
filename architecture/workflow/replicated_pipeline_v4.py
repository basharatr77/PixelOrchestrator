import asyncio
from architecture.core.replicated_broker_v4 import ReplicatedBrokerV4

broker = ReplicatedBrokerV4(["n1","n2","n3"])

async def handler(event):
    print("EVENT:", event)

async def main():
    broker.subscribe("group-1", handler)
    broker.subscribe("group-2", handler)

    asyncio.create_task(broker.start())

    for i in range(10):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i%3}"}
        })

    await asyncio.sleep(3)

asyncio.run(main())
