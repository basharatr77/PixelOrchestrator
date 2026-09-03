"""Task contract for PixelOrchestrator Phase 40.

A Task represents one requested execution unit:
device + module + action + parameters + execution state.

Queueing, execution, retry policy, workflow/DAG handling, and event
publishing are intentionally outside this contract.
"""

from dataclasses import dataclass, field
from enum import Enum
import time
import uuid
from typing import Any

from app.core.module_contract import ActionResult


class TaskStatus(str, Enum):
    """Lifecycle states for an executable task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Canonical execution request for Phase 40."""

    device_id: str
    module_id: str
    action_id: str
    parameters: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    result: ActionResult | None = None

    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None

    def __post_init__(self) -> None:
        """Validate the structural task contract."""

        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Task ID cannot be empty.")

        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise ValueError("Task device ID cannot be empty.")

        if not isinstance(self.module_id, str) or not self.module_id.strip():
            raise ValueError("Task module ID cannot be empty.")

        if not isinstance(self.action_id, str) or not self.action_id.strip():
            raise ValueError("Task action ID cannot be empty.")

        if not isinstance(self.parameters, dict):
            raise TypeError("Task parameters must be a dictionary.")

        if not isinstance(self.attempts, int) or self.attempts < 0:
            raise ValueError("Task attempts must be a non-negative integer.")

        if not isinstance(self.status, TaskStatus):
            try:
                self.status = TaskStatus(self.status)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid task status: {self.status!r}"
                ) from exc

        # Prevent later mutation of the caller's original dictionary
        # from silently changing the Task.
        self.parameters = dict(self.parameters)

    def start(self) -> None:
        """Move a pending task into execution."""

        if self.status is not TaskStatus.PENDING:
            raise ValueError(
                f"Task cannot start from status '{self.status.value}'."
            )

        self.status = TaskStatus.RUNNING
        self.attempts += 1

        if self.started_at is None:
            self.started_at = time.time()

    def complete(self, result: ActionResult) -> None:
        """Complete a running task successfully."""

        if self.status is not TaskStatus.RUNNING:
            raise ValueError(
                f"Task cannot complete from status '{self.status.value}'."
            )

        if not isinstance(result, ActionResult):
            raise TypeError("Task result must be an ActionResult.")

        self.result = result
        self.status = TaskStatus.COMPLETED
        self.completed_at = time.time()

    def retry(self, result: ActionResult) -> None:
        """Return a failed execution attempt to pending for another attempt."""

        if self.status is not TaskStatus.RUNNING:
            raise ValueError(
                f"Task cannot retry from status '{self.status.value}'."
            )

        if not isinstance(result, ActionResult):
            raise TypeError("Task retry result must be an ActionResult.")

        self.result = result
        self.status = TaskStatus.PENDING
        self.completed_at = None

    def fail(self, result: ActionResult) -> None:
        """Mark a running task as failed."""

        if self.status is not TaskStatus.RUNNING:
            raise ValueError(
                f"Task cannot fail from status '{self.status.value}'."
            )

        if not isinstance(result, ActionResult):
            raise TypeError("Task result must be an ActionResult.")

        self.result = result
        self.status = TaskStatus.FAILED
        self.completed_at = time.time()

    def cancel(self) -> None:
        """Cancel a pending or running task."""

        if self.status not in {
            TaskStatus.PENDING,
            TaskStatus.RUNNING,
        }:
            raise ValueError(
                f"Task cannot be cancelled from status '{self.status.value}'."
            )

        self.status = TaskStatus.CANCELLED
        self.completed_at = time.time()
