from architecture.storage.event_store import EventStore
from architecture.storage.replay_engine import ReplayEngine

store = EventStore()
replay = ReplayEngine(store)

def print_event(event):
    print("\n🔁 REPLAY EVENT")
    print(event)

replay.replay_all(print_event)
