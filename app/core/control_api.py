from db.database import add_device

def handle_event(event, bus):
    print("CONTROL API EVENT:", event)

    if event.get("type") == "DEVICE_CONNECTED":
        add_device(event.get("payload"))
        bus.publish(event)
