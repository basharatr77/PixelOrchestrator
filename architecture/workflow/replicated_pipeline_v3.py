import asyncio
from architecture.core.replicated_broker_v3 import ReplicatedBrokerV3

broker = ReplicatedBrokerV3(["n1","n2","n3"])

async def handler(event):
    print("EVENT:", event)

async def main():
    broker.subscribe("c1", handler)
    broker.subscribe("c2", handler)

    asyncio.create_task(broker.start())

    for i in range(10):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i%3}"}
        })

    await asyncio.sleep(3)

asyncio.run(main())
