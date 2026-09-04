from app.core.task import Task
from app.core.workflow import Workflow


class WorkflowExecutor:
    """Orchestration boundary for scheduling ready workflow tasks."""

    def __init__(self, task_queue):
        self.task_queue = task_queue

    def enqueue_ready_tasks(self, workflow):
        if not isinstance(workflow, Workflow):
            raise TypeError("WorkflowExecutor requires a Workflow.")

        ready = workflow.ready_tasks()

        for task in ready:
            self.task_queue.add_task(task)

        return ready
