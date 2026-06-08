from architecture.events.event_engine import EventEngine
from architecture.ai.ai_router import AIRouter
from architecture.workflow.executor import Executor
from architecture.core.device_state import DeviceState

engine = EventEngine()
ai = AIRouter()
executor = Executor()

device = DeviceState("pixel-1")

def handle_event(data):
    event = {"type": "DEVICE_DETECTED", "data": data}

    decision = ai.decide(event)
    result = executor.execute(decision, data)

    state_update = device.update(result["status"])

    print("DECISION:", decision)
    print("RESULT:", result)
    print("STATE:", state_update)

engine.subscribe("DEVICE_DETECTED", handle_event)
engine.emit("DEVICE_DETECTED", {"id": "pixel-1"})
