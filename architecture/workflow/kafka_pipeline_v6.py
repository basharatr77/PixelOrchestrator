import asyncio
from architecture.core.kafka_broker_v6 import KafkaBrokerV6

broker = KafkaBrokerV6()

async def handler(event):
    print("[PROCESS]", event)

async def main():
    broker.subscribe("c1", "DEVICE_DETECTED", handler)
    broker.subscribe("c2", "DEVICE_DETECTED", handler)

    for i in range(15):
        broker.publish("DEVICE_DETECTED", {
            "id": f"pixel-{i%3}"
        })

    await broker.start()

asyncio.run(main())
