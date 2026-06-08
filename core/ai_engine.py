class AIDecisionEngine:

    def __init__(self, queue, workflow):
        self.queue = queue
        self.workflow = workflow

    async def process(self, event_type, data):

        print(f"[AI ENGINE] {event_type} -> {data}")

        if event_type == "device.connected":
            return await self.workflow.start_workflow(
                data,
                ["flash", "verify", "install_tools"]
            )

        if event_type == "device.error":
            return await self.workflow.start_workflow(
                data,
                ["diagnose", "repair", "reboot"]
            )

        print("[AI ENGINE] No rule matched")
