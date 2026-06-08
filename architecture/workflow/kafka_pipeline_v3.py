import asyncio
from architecture.core.kafka_broker_v3 import KafkaBrokerV3

broker = KafkaBrokerV3()

async def handler(event):
    print("PROCESS:", event)

async def main():
    broker.subscribe("c1", "DEVICE_DETECTED", handler)
    broker.subscribe("c2", "DEVICE_DETECTED", handler)

    asyncio.create_task(broker.start())

    for i in range(10):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i%3}"}
        })

    await asyncio.sleep(3)

asyncio.run(main())
