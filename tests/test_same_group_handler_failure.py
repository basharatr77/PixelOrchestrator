import asyncio

from app.core.event_bus import StreamBus
from app.core.events import Event


def test_same_group_failed_handler_does_not_break_other_handlers():
    async def run():
        bus = StreamBus()

        group_id = "same-group-failure-isolation-test"

        handled = []
        should_fail = {"value": True}

        def handler_a(event, offset, group_id):
            handled.append("A")

        def handler_b(event, offset, group_id):
            handled.append("B")

            if should_fail["value"]:
                should_fail["value"] = False
                raise RuntimeError("temporary failure")

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

        first_commit = bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        )

        await bus.dispatch(offset, event)

        assert handled == ["A", "B", "A", "B"]

        second_commit = bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        )

        assert second_commit == offset

    asyncio.run(run())
