import asyncio

from app.core.event_bus import StreamBus
from app.core.events import Event


def test_consumer_offset_commits_after_success():
    async def run():
        bus = StreamBus()

        handled = []

        def handler(event, offset, group_id):
            handled.append(event.type)

        bus.subscribe(
            "offset-success-test",
            "TEST_EVENT",
            handler,
        )

        event = Event(
            "TEST_EVENT",
            {"value": 1},
        )

        offset = bus.log.append(event)

        await bus.dispatch(offset, event)

        assert handled == ["TEST_EVENT"]

        assert bus.consumer_store.get_offset(
            "offset-success-test",
            "TEST_EVENT",
        ) == offset

    asyncio.run(run())


def test_consumer_offset_is_not_committed_when_handler_fails():
    async def run():
        bus = StreamBus()

        attempts = []

        def failing_handler(event, offset, group_id):
            attempts.append(event.type)
            raise RuntimeError("handler failure")

        group_id = "offset-failure-test"

        bus.subscribe(
            group_id,
            "TEST_EVENT",
            failing_handler,
        )

        event = Event(
            "TEST_EVENT",
            {"value": 1},
        )

        offset = bus.log.append(event)

        baseline = bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        )

        await bus.dispatch(offset, event)

        assert attempts == ["TEST_EVENT"]

        assert bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        ) == baseline

    asyncio.run(run())


def test_same_event_can_be_retried_after_handler_failure():
    async def run():
        bus = StreamBus()

        attempts = []
        should_fail = {"value": True}

        group_id = "offset-retry-test"

        def handler(event, offset, group_id):
            attempts.append(event.type)

            if should_fail["value"]:
                should_fail["value"] = False
                raise RuntimeError("temporary failure")

        bus.subscribe(
            group_id,
            "TEST_EVENT",
            handler,
        )

        event = Event(
            "TEST_EVENT",
            {"value": 1},
        )

        offset = bus.log.append(event)

        baseline = bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        )

        await bus.dispatch(offset, event)

        assert bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        ) == baseline

        await bus.dispatch(offset, event)

        assert attempts == [
            "TEST_EVENT",
            "TEST_EVENT",
        ]

        assert bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        ) == offset

    asyncio.run(run())
