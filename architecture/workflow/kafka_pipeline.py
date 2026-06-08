import asyncio
from architecture.core.kafka_broker import KafkaStyleBroker
from architecture.ai.ai_router import AIRouter
from architecture.workflow.executor import Executor
from architecture.core.device_state import DeviceState

broker = KafkaStyleBroker()
ai = AIRouter()
executor = Executor()
device = DeviceState("pixel-1")

async def handler(event):
    decision = ai.decide(event)
    result = executor.execute(decision, event["data"])
    state = device.update(result["status"])

    print("\nEVENT:", event)
    print("DECISION:", decision)
    print("RESULT:", result)
    print("STATE:", state)

async def main():
    broker.subscribe("consumer-1", "DEVICE_DETECTED", handler)

    asyncio.create_task(broker.start())

    await broker.publish("DEVICE_DETECTED", {
        "type": "DEVICE_DETECTED",
        "data": {"id": "pixel-1"}
    })

    await asyncio.sleep(2)

asyncio.run(main())
