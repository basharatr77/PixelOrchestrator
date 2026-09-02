from collections import deque


class TaskQueue:
    """FIFO task queue used by the orchestration runtime."""

    def __init__(self):
        self._tasks = deque()

    @property
    def tasks(self):
        """Return a list-compatible view for existing runtime callers."""
        return list(self._tasks)

    def add_task(self, task):
        print("\U0001F9E9 TASK:", task)
        self._tasks.append(task)

    def pop_task(self):
        if self._tasks:
            return self._tasks.popleft()
        return None

    def peek_task(self):
        if self._tasks:
            return self._tasks[0]
        return None

    def size(self):
        return len(self._tasks)

    def is_empty(self):
        return not self._tasks

    def clear(self):
        self._tasks.clear()
