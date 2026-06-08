<<<<<<< HEAD
import asyncio
=======
<<<<<<< HEAD
from core.stable_bus import StableEventBus
>>>>>>> 57b558f (auto update)

from core.event_bus import EventBus
from core.task_queue import TaskQueue
from core.workflow_engine import WorkflowEngine
from core.event_types import EventTypes

from core.event_store import EventStore
from core.replay_engine import ReplayEngine
from core.ai_engine import AIDecisionEngine


REPLAY_DONE = False   # ✅ GLOBAL GUARD


async def main():

    global REPLAY_DONE

    store = EventStore()
    bus = EventBus(store)
    queue = TaskQueue()

<<<<<<< HEAD
=======
print("System running (STABLE MODE) 🚀")
=======
import asyncio

from core.event_bus import EventBus
from core.task_queue import TaskQueue
from core.workflow_engine import WorkflowEngine
from core.event_types import EventTypes

from core.event_store import EventStore
from core.replay_engine import ReplayEngine
from core.ai_engine import AIDecisionEngine


REPLAY_DONE = False   # ✅ GLOBAL GUARD


async def main():

    global REPLAY_DONE

    store = EventStore()
    bus = EventBus(store)
    queue = TaskQueue()

>>>>>>> 57b558f (auto update)
    workflow = WorkflowEngine(bus, queue)
    ai_engine = AIDecisionEngine(queue, workflow)

    async def on_device_connected(data):
        await ai_engine.process("device.connected", data)

    async def on_device_error(data):
        await ai_engine.process("device.error", data)

    bus.subscribe(EventTypes.DEVICE_CONNECTED, on_device_connected)
    bus.subscribe(EventTypes.DEVICE_ERROR, on_device_error)

    # ✅ RUN REPLAY ONLY ONCE
    if not REPLAY_DONE:
        replay = ReplayEngine(store, bus)
        await replay.replay()
        REPLAY_DONE = True

    asyncio.create_task(queue.worker())

    await bus.publish(EventTypes.DEVICE_CONNECTED, "PIXEL_8")

    await asyncio.sleep(10)


asyncio.run(main())
<<<<<<< HEAD
=======
>>>>>>> 0900c60 (Stable Event-Driven Core: AI engine, workflow, dedup, replay fix, async event bus hardened)
>>>>>>> 57b558f (auto update)
