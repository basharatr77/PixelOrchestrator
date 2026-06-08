class TaskQueue:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        print("🧩 TASK ADDED:", task)
        self.tasks.append(task)

    def get_tasks(self):
        return self.tasks

    def pop_task(self):
        if self.tasks:
            return self.tasks.pop(0)
        return None
