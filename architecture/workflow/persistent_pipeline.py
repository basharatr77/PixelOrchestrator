from architecture.events.event_engine import EventEngine
from architecture.ai.ai_router import AIRouter
from architecture.workflow.executor import Executor
from architecture.core.device_state import DeviceState
from architecture.storage.event_store import EventStore

engine = EventEngine()
ai = AIRouter()
executor = Executor()
store = EventStore()

device = DeviceState("pixel-1")

def handle_event(data):
    event = {"type": "DEVICE_DETECTED", "data": data}

    store.save(event)  # 🔥 persistence

    decision = ai.decide(event)
    result = executor.execute(decision, data)
    state = device.update(result["status"])

    print("EVENT:", event)
    print("DECISION:", decision)
    print("RESULT:", result)
    print("STATE:", state)

engine.subscribe("DEVICE_DETECTED", handle_event)
engine.emit("DEVICE_DETECTED", {"id": "pixel-1"})
