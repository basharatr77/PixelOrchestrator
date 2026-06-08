from architecture.events.event_engine import EventEngine
from architecture.ai.ai_router import AIRouter
from architecture.workflow.executor import Executor

engine = EventEngine()
ai = AIRouter()
executor = Executor()

def handle_event(data):
    event = {"type": "DEVICE_DETECTED", "data": data}

    decision = ai.decide(event)
    result = executor.execute(decision, data)

    print("DECISION:", decision)
    print("RESULT:", result)

engine.subscribe("DEVICE_DETECTED", handle_event)

engine.emit("DEVICE_DETECTED", {"id": "pixel-1"})
