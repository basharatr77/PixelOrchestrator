from unified_event_bus import UnifiedEventBus

bus = UnifiedEventBus()

def handler(data):
    print("EVENT RECEIVED:", data)

bus.subscribe("DEVICE_DETECTED", handler)

bus.publish("DEVICE_DETECTED", {"id": "pixel-1", "status": "online"})
