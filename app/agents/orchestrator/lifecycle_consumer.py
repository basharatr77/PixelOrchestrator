from app.agents.orchestrator.ai_engine import decide
from app.core.module_contract import Device, DeviceState, ModuleType
from app.core.device_state import DeviceStateMachine


class LifecycleConsumer:
    GROUP_ID = "orchestrator"

    def __init__(
        self,
        task_queue,
        registry_updater,
        device_registry=None,
    ):
        self.task_queue = task_queue
        self.registry_updater = registry_updater
        self.device_registry = device_registry

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

    @staticmethod
    def _state_from_mode(mode):
        mapping = {
            "ADB": DeviceState.ADB,
            "FASTBOOT": DeviceState.FASTBOOT,
            "FASTBOOTD": DeviceState.FASTBOOTD,
            "RECOVERY": DeviceState.RECOVERY,
            "SIDELOAD": DeviceState.SIDELOAD,
            "EDL": DeviceState.EDL,
            "BROM": DeviceState.BROM,
            "PRELOADER": DeviceState.PRELOADER,
            "DOWNLOAD": DeviceState.DOWNLOAD,
        }

        return mapping.get(str(mode).upper(), DeviceState.UNKNOWN)

    def _canonical_device(self, payload):
        if self.device_registry is None:
            return None

        serial = payload["serial"]
        mode = payload.get("mode", "UNKNOWN")
        target_state = self._state_from_mode(mode)

        device_id = f"device:{serial}"

        device = self.device_registry.get(device_id)

        if device is None:
            device = Device(
                device_id=device_id,
                module_type=(
                    ModuleType.ADB
                    if target_state is DeviceState.ADB
                    else ModuleType.FASTBOOT
                    if target_state is DeviceState.FASTBOOT
                    else ModuleType.COMMON
                ),
                state=DeviceState.UNKNOWN,
                model=payload.get("model") or None,
                serial=serial,
                transport=str(mode).lower(),
                properties={
                    "brand": payload.get("brand", ""),
                    "android_version": payload.get(
                        "android_version",
                        "",
                    ),
                },
            )

            self.device_registry.register(device)

        if target_state is not DeviceState.UNKNOWN:
            if device.state is not target_state:
                DeviceStateMachine.transition(
                    device,
                    target_state,
                )

        return device

    def handle(self, event, offset, group_id):
        payload = event.payload
        event_type = event.type

        serial = payload["serial"]

        if event_type == "DEVICE_CONNECTED":
            mode = payload["mode"]

            self._canonical_device(payload)

            accepted = self.registry_updater(
                serial,
                mode,
                offset,
            )

            if accepted:
                self.task_queue.add_task(
                    decide({
                        "serial": serial,
                        "mode": mode,
                    })
                )

        elif event_type == "DEVICE_MODE_CHANGED":
            mode = payload["mode"]

            self._canonical_device(payload)

            accepted = self.registry_updater(
                serial,
                mode,
                offset,
            )

            if accepted:
                self.task_queue.add_task(
                    decide({
                        "serial": serial,
                        "mode": mode,
                    })
                )

        elif event_type == "DEVICE_DISCONNECTED":
            if self.device_registry is not None:
                device = self.device_registry.get(
                    f"device:{serial}"
                )

                if device is not None:
                    DeviceStateMachine.transition(
                        device,
                        DeviceState.DISCONNECTED,
                    )

            self.registry_updater(
                serial,
                "disconnected",
                offset,
            )
