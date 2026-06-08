import asyncio
from architecture.core.replicated_broker_v2 import ReplicatedBrokerV2

broker = ReplicatedBrokerV2(["n1","n2","n3"])

async def handler(event):
    print("EVENT:", event)

async def main():
    broker.subscribe("n1", handler)
    broker.subscribe("n2", handler)

    asyncio.create_task(broker.start())

    for i in range(10):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i%3}"}
        })

    await asyncio.sleep(3)

asyncio.run(main())
