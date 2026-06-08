import asyncio
from architecture.core.persistent_broker import PersistentEventBroker
from architecture.ai.ai_router import AIRouter
from architecture.workflow.executor import Executor
from architecture.core.device_state import DeviceState

broker = PersistentEventBroker()
ai = AIRouter()
executor = Executor()
device = DeviceState("pixel-1")

async def handle(event):
    decision = ai.decide(event)
    result = executor.execute(decision, event["data"])
    state = device.update(result["status"])

    print("\nEVENT:", event)
    print("DECISION:", decision)
    print("RESULT:", result)
    print("STATE:", state)

async def main():
    broker.subscribe("DEVICE_DETECTED", handle)

    asyncio.create_task(broker.start())

    await broker.publish("DEVICE_DETECTED", {
        "type": "DEVICE_DETECTED",
        "data": {"id": "pixel-1"}
    })

    await asyncio.sleep(2)

asyncio.run(main())
