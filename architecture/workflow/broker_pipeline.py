from architecture.core.event_broker import EventBroker
from architecture.ai.ai_router import AIRouter
from architecture.workflow.executor import Executor
from architecture.core.device_state import DeviceState

broker = EventBroker()
ai = AIRouter()
executor = Executor()
device = DeviceState("pixel-1")

# ---------------------------
# HANDLER
# ---------------------------
def handle_device_event(event):
    decision = ai.decide(event)
    result = executor.execute(decision, event["data"])
    state = device.update(result["status"])

    print("\nEVENT  :", event)
    print("DECISION:", decision)
    print("RESULT  :", result)
    print("STATE   :", state)

# ---------------------------
# SUBSCRIBE
# ---------------------------
broker.subscribe("DEVICE_DETECTED", handle_device_event)

# start broker loop
broker.start()

# ---------------------------
# PUBLISH EVENTS
# ---------------------------
broker.publish("DEVICE_DETECTED", {
    "type": "DEVICE_DETECTED",
    "data": {"id": "pixel-1"}
})

broker.publish("DEVICE_DETECTED", {
    "type": "DEVICE_DETECTED",
    "data": {"id": "pixel-1"}
})

# keep alive
import time
time.sleep(3)
