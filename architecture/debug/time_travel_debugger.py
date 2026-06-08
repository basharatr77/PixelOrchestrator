from architecture.storage.event_store import EventStore
from architecture.ai.ai_router import AIRouter
from architecture.workflow.executor import Executor
from architecture.core.device_state import DeviceState
import time

class TimeTravelDebugger:
    def __init__(self):
        self.store = EventStore()
        self.ai = AIRouter()
        self.executor = Executor()

    def step_replay(self, device_id, delay=1):
        events = self.store.load_all()
        device = DeviceState(device_id)

        step = 0

        for event in events:
            if event["data"].get("id") != device_id:
                continue

            step += 1
            print("\n━━━━━━━━ STEP", step, "━━━━━━━━")

            decision = self.ai.decide(event)
            result = self.executor.execute(decision, event["data"])
            state = device.update(result["status"])

            print("EVENT   :", event)
            print("DECISION:", decision)
            print("RESULT  :", result)
            print("STATE   :", state)

            time.sleep(delay)
