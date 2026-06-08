from architecture.events.event_engine import EventEngine
from architecture.ai.ai_router import AIRouter

engine = EventEngine()
ai = AIRouter()

def handle_event(data):
    decision = ai.decide({"type": "DEVICE_DETECTED", "data": data})
    print("AI DECISION:", decision)

engine.subscribe("DEVICE_DETECTED", handle_event)

engine.emit("DEVICE_DETECTED", {"id": "pixel-1"})
