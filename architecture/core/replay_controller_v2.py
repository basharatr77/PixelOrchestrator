from architecture.storage.replay_engine_v2 import ReplayEngineV2

class ReplayControllerV2:
    def __init__(self, broker):
        self.engine = ReplayEngineV2(broker.commit_log)

    def replay_topic(self, topic, handler, from_offset=0):
        print(f"[REPLAY v2] topic={topic} from_offset={from_offset}")
        self.engine.replay(handler, topic, from_offset)
