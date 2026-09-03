import time
import uuid


class Event:
    def __init__(self, type, payload):
        self.id = str(uuid.uuid4())
        self.type = type

        if type == "TASK_PROGRESS":
            self._validate_task_progress_payload(payload)

        self.payload = payload
        self.ts = time.time()

    @staticmethod
    def _validate_task_progress_payload(payload):
        if not isinstance(payload, dict):
            raise TypeError(
                "TASK_PROGRESS payload must be a dictionary."
            )

        task_id = payload.get("task_id")

        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError(
                "TASK_PROGRESS payload requires a non-empty task_id."
            )

        if "progress" not in payload:
            raise ValueError(
                "TASK_PROGRESS payload requires progress."
            )

        progress = payload["progress"]

        if isinstance(progress, bool) or not isinstance(progress, int):
            raise TypeError(
                "TASK_PROGRESS progress must be an integer."
            )

        if not 0 <= progress <= 100:
            raise ValueError(
                "TASK_PROGRESS progress must be between 0 and 100."
            )

        if "message" in payload and not isinstance(
            payload["message"], str
        ):
            raise TypeError(
                "TASK_PROGRESS message must be a string."
            )
