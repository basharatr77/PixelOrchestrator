"""Retry policy contract for PixelOrchestrator Phase 40-F."""

from dataclasses import dataclass

from app.core.module_contract import ActionResult


@dataclass(frozen=True)
class RetryPolicy:
    """Define whether a failed task execution may be attempted again."""

    max_attempts: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.max_attempts, int):
            raise TypeError("RetryPolicy max_attempts must be an integer.")

        if self.max_attempts < 1:
            raise ValueError("RetryPolicy max_attempts must be at least 1.")

    def should_retry(self, attempts: int, result: ActionResult) -> bool:
        """Return True when a failed result may be retried."""

        if not isinstance(attempts, int) or attempts < 1:
            raise ValueError("RetryPolicy attempts must be a positive integer.")

        if not isinstance(result, ActionResult):
            raise TypeError("RetryPolicy result must be an ActionResult.")

        if result.success:
            return False

        return attempts < self.max_attempts
