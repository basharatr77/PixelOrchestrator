from app.core.task import Task, TaskStatus


class ExecutionWorker:
    def __init__(self, task_queue, executor):
        self.task_queue = task_queue
        self.executor = executor

    def run_once(self):
        task = self.task_queue.pop_task()

        if task is None:
            return None

        if isinstance(task, Task) and task.status is TaskStatus.CANCELLED:
            return None

        return self.executor.execute(task)
