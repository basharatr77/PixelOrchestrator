from app.core.task import Task
from app.core.workflow import Workflow


class WorkflowExecutor:
    """Orchestration boundary for scheduling ready workflow tasks."""

    def __init__(self, task_queue):
        self.task_queue = task_queue
        self._workflows = {}

    def _queued_task_ids(self):
        return {
            task.id
            for task in self.task_queue.tasks
            if isinstance(task, Task)
        }

    def enqueue_ready_tasks(self, workflow):
        if not isinstance(workflow, Workflow):
            raise TypeError("WorkflowExecutor requires a Workflow.")

        self._workflows[workflow.id] = workflow

        queued_task_ids = self._queued_task_ids()
        ready = workflow.ready_tasks()
        enqueued = []

        for task in ready:
            if task.id in queued_task_ids:
                continue

            self.task_queue.add_task(task)
            queued_task_ids.add(task.id)
            enqueued.append(task)

        return enqueued

    def advance(self):
        """Re-evaluate tracked workflows and enqueue newly ready tasks."""
        enqueued = []

        for workflow in self._workflows.values():
            enqueued.extend(self.enqueue_ready_tasks(workflow))

        return enqueued

    def on_task_executed(self, task):
        """Advance tracked workflows after a canonical Task execution."""
        if not isinstance(task, Task):
            return []

        return self.advance()
