import asyncio

from app.core.event_bus import StreamBus
from app.core.events import Event


def test_same_group_handlers_share_event_processing_semantics():
    async def run():
        bus = StreamBus()

        group_id = "same-group-handlers-test"

        handled = []

        def handler_a(event, offset, group_id):
            handled.append("A")

        def handler_b(event, offset, group_id):
            handled.append("B")

        bus.subscribe(
            group_id,
            "TEST_EVENT",
            handler_a,
        )

        bus.subscribe(
            group_id,
            "TEST_EVENT",
            handler_b,
        )

        event = Event(
            "TEST_EVENT",
            {"value": 1},
        )

        offset = bus.log.append(event)

        await bus.dispatch(offset, event)

        assert handled == ["A", "B"]

        assert bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        ) == offset

    asyncio.run(run())
