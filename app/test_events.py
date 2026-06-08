import time
import random
from app.core.control_bus import ControlBus

bus = ControlBus()

devices = ["Samsung A52", "Pixel 6", "Redmi Note 12", "iPhone 13"]

def fake_stream():
    while True:
        event = {
            "type": "DEVICE_CONNECTED",
            "payload": random.choice(devices)
        }
        bus.publish(event)
        time.sleep(2)

fake_stream()
