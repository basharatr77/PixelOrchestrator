from architecture.storage.replay_engine import ReplayEngine

class ReplayController:
    def __init__(self, broker):
        self.engine = ReplayEngine(broker.commit_log)

    def replay_topic(self, topic, handler):
        print(f"[REPLAY] Replaying topic: {topic}")
        self.engine.replay(handler, topic)
