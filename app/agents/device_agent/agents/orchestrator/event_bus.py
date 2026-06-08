import time
from collections import deque

class EventBus:
    def __init__(self):
        self.queue = deque()

    def publish(self, event):
        print("📡 EVENT:", event)
        self.queue.append(event)

    def get_event(self):
        if self.queue:
            return self.queue.popleft()
        return None
