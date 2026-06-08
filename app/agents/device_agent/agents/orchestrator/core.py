import time

from app.agents.orchestrator.event_bus import EventBus
from app.agents.orchestrator.ai_engine import decide
from app.agents.orchestrator.task_queue import TaskQueue

bus = EventBus()
queue = TaskQueue()

print("🚀 AI Orchestration Layer Started")

def simulate_device_stream():
    # This will later connect to your detector
    return [
        {"serial": "ABC123456789", "mode": "ADB"},
        {"serial": "FASTBOOT_XYZ", "mode": "FASTBOOT"}
    ]

while True:
    devices = simulate_device_stream()

    for d in devices:
        event = {"type": "DEVICE_DETECTED", "data": d}
        bus.publish(event)

        decision = decide(d)

        queue.add_task(decision)

    # Process tasks
    task = queue.pop_task()
    if task:
        print("⚡ EXECUTING:", task)

    time.sleep(5)
