import asyncio
from architecture.core.event_raft_broker import EventRaftBroker

broker = EventRaftBroker()

async def handler(event):
    print("PROCESS:", event)

async def main():
    broker.register_node("n1")
    broker.register_node("n2")
    broker.register_node("n3")

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
