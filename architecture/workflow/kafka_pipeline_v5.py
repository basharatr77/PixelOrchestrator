import asyncio
from architecture.core.kafka_broker_v5 import KafkaBrokerV5

broker = KafkaBrokerV5()

async def handler(event):
    print("PROCESS:", event)

async def main():
    broker.subscribe("group-1", "c1", "DEVICE_DETECTED", handler)
    broker.subscribe("group-1", "c2", "DEVICE_DETECTED", handler)

    asyncio.create_task(broker.start())

    # simulate heartbeat
    broker.heartbeat("c1")
    broker.heartbeat("c2")

    for i in range(8):
        broker.publish("DEVICE_DETECTED", {
            "type": "DEVICE_DETECTED",
            "data": {"id": f"pixel-{i%3}"}
        })

    await asyncio.sleep(3)

asyncio.run(main())
