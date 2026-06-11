from architecture.core.event_stream_core import EventStreamCore

class ControlPlane:
    def __init__(self):
        self.stream = EventStreamCore()
        self.devices = {}
        self.running = False

    async def start(self):
        self.running = True
        await self.stream.start()
        print("[CONTROL] Control Plane ONLINE")

    async def stop(self):
        self.running = False
        await self.stream.stop()
        print("[CONTROL] Control Plane STOPPED")

    def get_event_bus(self):
        return self.stream

    def health(self):
        return {
            "devices": len(self.devices),
            "status": "running" if self.running else "stopped",
            "events_buffer": len(self.stream.event_log)
        }
