class TaskQueue:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        print("🧩 TASK:", task)
        self.tasks.append(task)

    def pop_task(self):
        if self.tasks:
            return self.tasks.pop(0)
        return None
