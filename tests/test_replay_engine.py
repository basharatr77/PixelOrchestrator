import asyncio
import sqlite3

from core.event_store import EventStore
from core.event_bus import EventBus
from core.replay_engine import ReplayEngine


def test_replay_delivers_all_events_without_persisting():
    async def run():
        conn = sqlite3.connect("events.db")
        before = conn.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        conn.close()

        store = EventStore()
        bus = EventBus(store)
        replay = ReplayEngine(store, bus)

        received = []

        async def on_event(data):
            received.append(data)

        bus.subscribe("device.connected", on_event)
        bus.subscribe("device.test", on_event)

        await replay.replay()

        conn = sqlite3.connect("events.db")
        after = conn.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        conn.close()

        assert len(received) == before
        assert after == before

    asyncio.run(run())
