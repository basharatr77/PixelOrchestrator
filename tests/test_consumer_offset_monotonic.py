import asyncio

from app.core.event_bus import StreamBus
from app.core.events import Event


def test_consumer_offset_never_moves_backward():
    async def run():
        bus = StreamBus()

        group_id = "offset-monotonic-test"
        committed = []

        async def handler(event, offset, group_id):
            committed.append(offset)

        bus.subscribe(
            group_id,
            "TEST_EVENT",
            handler,
        )

        event1 = Event(
            "TEST_EVENT",
            {"value": 1},
        )

        event2 = Event(
            "TEST_EVENT",
            {"value": 2},
        )

        offset1 = bus.log.append(event1)
        offset2 = bus.log.append(event2)

        await bus.dispatch(offset2, event2)
        assert bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        ) == offset2

        await bus.dispatch(offset1, event1)

        assert bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        ) == offset2

    asyncio.run(run())
