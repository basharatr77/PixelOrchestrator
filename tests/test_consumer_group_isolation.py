import asyncio

from app.core.event_bus import StreamBus
from app.core.events import Event


def test_consumer_groups_have_independent_offsets():
    async def run():
        bus = StreamBus()

        handled_a = []
        handled_b = []

        def handler_a(event, offset, group_id):
            handled_a.append(event.type)

        def handler_b(event, offset, group_id):
            handled_b.append(event.type)

        bus.subscribe(
            "group-a-isolation-test",
            "TEST_EVENT",
            handler_a,
        )

        bus.subscribe(
            "group-b-isolation-test",
            "TEST_EVENT",
            handler_b,
        )

        event = Event(
            "TEST_EVENT",
            {"value": 1},
        )

        offset = bus.log.append(event)

        await bus.dispatch(offset, event)

        assert handled_a == ["TEST_EVENT"]
        assert handled_b == ["TEST_EVENT"]

        assert bus.consumer_store.get_offset(
            "group-a-isolation-test",
            "TEST_EVENT",
        ) == offset

        assert bus.consumer_store.get_offset(
            "group-b-isolation-test",
            "TEST_EVENT",
        ) == offset

    asyncio.run(run())


def test_committed_offset_in_one_group_does_not_block_another_group():
    async def run():
        bus = StreamBus()

        handled_a = []
        handled_b = []

        def handler_a(event, offset, group_id):
            handled_a.append(event.type)

        def handler_b(event, offset, group_id):
            handled_b.append(event.type)

        bus.subscribe(
            "group-a-independent-test",
            "TEST_EVENT",
            handler_a,
        )

        bus.subscribe(
            "group-b-independent-test",
            "TEST_EVENT",
            handler_b,
        )

        event = Event(
            "TEST_EVENT",
            {"value": 1},
        )

        offset = bus.log.append(event)

        await bus.dispatch(offset, event)

        assert handled_a == ["TEST_EVENT"]
        assert handled_b == ["TEST_EVENT"]

        next_event = Event(
            "TEST_EVENT",
            {"value": 2},
        )

        next_offset = bus.log.append(next_event)

        await bus.dispatch(next_offset, next_event)

        assert handled_a == [
            "TEST_EVENT",
            "TEST_EVENT",
        ]

        assert handled_b == [
            "TEST_EVENT",
            "TEST_EVENT",
        ]

        assert bus.consumer_store.get_offset(
            "group-a-independent-test",
            "TEST_EVENT",
        ) == next_offset

        assert bus.consumer_store.get_offset(
            "group-b-independent-test",
            "TEST_EVENT",
        ) == next_offset

    asyncio.run(run())
