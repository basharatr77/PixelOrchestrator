class DeviceState:
    def __init__(self, device_id):
        self.device_id = device_id
        self.state = "IDLE"

    def update(self, new_state):
        self.state = new_state
        return {
            "device_id": self.device_id,
            "state": self.state
        }
