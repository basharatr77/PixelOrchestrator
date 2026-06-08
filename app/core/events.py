import time
import uuid

class Event:
    def __init__(self, type, payload):
        self.id = str(uuid.uuid4())
        self.type = type
        self.payload = payload
        self.ts = time.time()
