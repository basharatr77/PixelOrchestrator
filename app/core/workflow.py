"""Workflow contract for PixelOrchestrator Phase 40.

A Workflow groups canonical Tasks and describes their dependency
relationships. Execution, queueing, retry policy, cancellation,
progress reporting, and failure handling remain outside this contract.
"""

from dataclasses import dataclass, field
import uuid

from app.core.task import Task, TaskStatus


@dataclass
class Workflow:
    """Canonical workflow definition for Phase 40."""

    tasks: list[Task] = field(default_factory=list)
    dependencies: dict[str, set[str]] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """Validate the structural workflow contract."""

        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Workflow ID cannot be empty.")

        if not isinstance(self.tasks, list):
            raise TypeError("Workflow tasks must be a list.")

        for task in self.tasks:
            if not isinstance(task, Task):
                raise TypeError("Workflow must contain Task objects.")

        task_ids = [task.id for task in self.tasks]

        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Workflow cannot contain duplicate task IDs.")

        if not isinstance(self.dependencies, dict):
            raise TypeError("Workflow dependencies must be a dictionary.")

        known_ids = set(task_ids)
        normalized: dict[str, set[str]] = {}

        for task_id, dependency_ids in self.dependencies.items():
            if task_id not in known_ids:
                raise ValueError(
                    f"Dependency target task '{task_id}' is not in the workflow."
                )

            if not isinstance(dependency_ids, (set, frozenset, list, tuple)):
                raise TypeError(
                    "Workflow dependency values must be collections of task IDs."
                )

            dependency_set = set(dependency_ids)

            unknown = dependency_set - known_ids
            if unknown:
                raise ValueError(
                    "Workflow dependency references unknown task IDs: "
                    + ", ".join(sorted(str(item) for item in unknown))
                )

            if task_id in dependency_set:
                raise ValueError(
                    f"Task '{task_id}' cannot depend on itself."
                )

            normalized[task_id] = dependency_set

        self.tasks = list(self.tasks)
        self.dependencies = normalized

    def validate_dag(self) -> bool:
        """Validate that workflow dependencies form an acyclic graph."""

        task_ids = {task.id for task in self.tasks}
        visiting = set()
        visited = set()

        def visit(task_id):
            if task_id in visiting:
                raise ValueError(
                    f"Workflow contains a dependency cycle involving task '{task_id}'."
                )

            if task_id in visited:
                return

            visiting.add(task_id)

            for dependency_id in self.dependencies.get(task_id, set()):
                if dependency_id not in task_ids:
                    raise ValueError(
                        f"Dependency references unknown task '{dependency_id}'."
                    )
                visit(dependency_id)

            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in task_ids:
            visit(task_id)

        return True

    def ready_tasks(self) -> list[Task]:
        """Return pending tasks whose dependencies are all completed."""

        ready = []

        for task in self.tasks:
            if task.status is not TaskStatus.PENDING:
                continue

            dependency_ids = self.dependencies.get(task.id, set())

            if all(
                dependency_task.status is TaskStatus.COMPLETED
                for dependency_task in self.tasks
                if dependency_task.id in dependency_ids
            ):
                ready.append(task)

        return ready
