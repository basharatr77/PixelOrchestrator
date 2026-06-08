import asyncio
from architecture.core.kafka_broker_v4 import KafkaBrokerV4

broker = KafkaBrokerV4()

async def handler(event):
    print("PROCESS:", event)

async def main():
    broker.subscribe("c1", "DEVICE_DETECTED", handler)
    broker.subscribe("c2", "DEVICE_DETECTED", handler)

    asyncio.create_task(broker.start())

    for i in range(6):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i%2}"}
        })

    await asyncio.sleep(2)

asyncio.run(main())
