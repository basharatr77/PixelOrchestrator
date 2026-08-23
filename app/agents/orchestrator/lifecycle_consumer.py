from app.agents.orchestrator.ai_engine import decide


class LifecycleConsumer:
    GROUP_ID = "orchestrator"

    def __init__(self, task_queue, registry_updater):
        self.task_queue = task_queue
        self.registry_updater = registry_updater

    def subscribe(self, bus):
        bus.subscribe(
            self.GROUP_ID,
            "DEVICE_CONNECTED",
            self.handle,
        )

        bus.subscribe(
            self.GROUP_ID,
            "DEVICE_MODE_CHANGED",
            self.handle,
        )

        bus.subscribe(
            self.GROUP_ID,
            "DEVICE_DISCONNECTED",
            self.handle,
        )

    def handle(self, event, offset, group_id):
        payload = event.payload
        event_type = event.type

        serial = payload["serial"]

        if event_type == "DEVICE_CONNECTED":
            mode = payload["mode"]

            self.registry_updater(
                serial,
                mode,
            )

            self.task_queue.add_task(
                decide({
                    "serial": serial,
                    "mode": mode,
                })
            )

        elif event_type == "DEVICE_MODE_CHANGED":
            mode = payload["mode"]

            self.registry_updater(
                serial,
                mode,
            )

            self.task_queue.add_task(
                decide({
                    "serial": serial,
                    "mode": mode,
                })
            )

        elif event_type == "DEVICE_DISCONNECTED":
            self.registry_updater(
                serial,
                "disconnected",
            )
