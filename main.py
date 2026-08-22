import asyncio

from core.event_bus import EventBus
from core.task_queue import TaskQueue
from core.workflow_engine import WorkflowEngine
from core.event_types import EventTypes
from core.event_store import EventStore
from core.replay_engine import ReplayEngine
from core.ai_engine import AIDecisionEngine


async def main():
    store = EventStore()
    bus = EventBus(store)
    queue = TaskQueue()

    workflow = WorkflowEngine(bus, queue)
    ai_engine = AIDecisionEngine(queue, workflow)

    async def on_device_connected(data):
        await ai_engine.process(EventTypes.DEVICE_CONNECTED, data)

    async def on_device_error(data):
        await ai_engine.process(EventTypes.DEVICE_ERROR, data)

    bus.subscribe(EventTypes.DEVICE_CONNECTED, on_device_connected)
    bus.subscribe(EventTypes.DEVICE_ERROR, on_device_error)

    asyncio.create_task(queue.worker())

    await bus.publish(
        EventTypes.DEVICE_CONNECTED,
        "PIXEL_8"
    )

    await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
