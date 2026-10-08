import asyncio

from app.core.event_bus import StreamBus
from app.core.events import Event
from app.core.worker_pool import WorkerPool


def test_worker_pool_processes_multiple_events():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=3)

        handled = []

        def handler(event, offset, group_id):
            handled.append(event.payload["value"])

        bus.subscribe(
            "concurrency-test",
            "TEST_EVENT",
            handler,
        )

        for value in range(10):
            await bus.publish(
                Event(
                    "TEST_EVENT",
                    {"value": value},
                )
            )

        await pool.start()

        await asyncio.wait_for(
            bus.queue.join(),
            timeout=2.0,
        )

        assert sorted(handled) == list(range(10))
        assert len(handled) == 10

        await pool.stop()

        assert pool.tasks == []

    asyncio.run(run())


def test_worker_pool_does_not_lose_events_with_multiple_workers():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=4)

        handled = []

        def handler(event, offset, group_id):
            handled.append(event.payload["value"])

        bus.subscribe(
            "multi-worker-loss-test",
            "TEST_EVENT",
            handler,
        )

        for value in range(50):
            await bus.publish(
                Event(
                    "TEST_EVENT",
                    {"value": value},
                )
            )

        await pool.start()

        await asyncio.wait_for(
            bus.queue.join(),
            timeout=3.0,
        )

        assert len(handled) == 50
        assert sorted(handled) == list(range(50))
        assert len(set(handled)) == 50

        await pool.stop()

    asyncio.run(run())


def test_failed_event_remains_retryable_after_later_offset_is_processed():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=2)
        group_id = "concurrent-failed-offset-test"
        first_started = asyncio.Event()
        release_first = asyncio.Event()
        attempts = []
        fail_first_attempt = True

        async def handler(event, offset, group_id):
            nonlocal fail_first_attempt
            value = event.payload["value"]
            attempts.append(value)

            if value == 1 and fail_first_attempt:
                fail_first_attempt = False
                first_started.set()
                await release_first.wait()
                raise RuntimeError("first event failed")

        bus.subscribe(group_id, "TEST_EVENT", handler)
        first_event = Event("TEST_EVENT", {"value": 1})
        second_event = Event("TEST_EVENT", {"value": 2})
        first_offset = await bus.publish(first_event)
        second_offset = await bus.publish(second_event)

        original_dispatch = bus.dispatch
        second_dispatch_started = asyncio.Event()

        async def tracked_dispatch(offset, event):
            if offset == second_offset:
                second_dispatch_started.set()
            await original_dispatch(offset, event)

        bus.dispatch = tracked_dispatch

        await pool.start()
        try:
            await asyncio.wait_for(first_started.wait(), timeout=1.0)
            await asyncio.wait_for(second_dispatch_started.wait(), timeout=1.0)
            release_first.set()
            await asyncio.wait_for(bus.queue.join(), timeout=1.0)

            await bus.dispatch(first_offset, first_event)
            await bus.dispatch(second_offset, second_event)

            assert attempts == [1, 1, 2]
            assert bus.consumer_store.get_offset(
                group_id,
                "TEST_EVENT",
            ) == second_offset
        finally:
            release_first.set()
            await pool.stop()

    asyncio.run(run())


def test_shutdown_cancellation_keeps_later_offset_from_skipping_active_event():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=2)
        group_id = "concurrent-cancelled-offset-test"
        first_started = asyncio.Event()
        attempts = []
        cancel_first_attempt = True

        async def handler(event, offset, group_id):
            nonlocal cancel_first_attempt
            value = event.payload["value"]
            attempts.append(value)

            if value == 1 and cancel_first_attempt:
                cancel_first_attempt = False
                first_started.set()
                await asyncio.Future()

        bus.subscribe(group_id, "TEST_EVENT", handler)
        first_event = Event("TEST_EVENT", {"value": 1})
        second_event = Event("TEST_EVENT", {"value": 2})
        first_offset = await bus.publish(first_event)
        second_offset = await bus.publish(second_event)

        original_dispatch = bus.dispatch
        second_dispatch_started = asyncio.Event()

        async def tracked_dispatch(offset, event):
            if offset == second_offset:
                second_dispatch_started.set()
            await original_dispatch(offset, event)

        bus.dispatch = tracked_dispatch

        await pool.start()
        await asyncio.wait_for(first_started.wait(), timeout=1.0)
        await asyncio.wait_for(second_dispatch_started.wait(), timeout=1.0)
        await pool.stop()

        await bus.dispatch(first_offset, first_event)
        await bus.dispatch(second_offset, second_event)

        assert attempts == [1, 1, 2]
        assert bus.consumer_store.get_offset(
            group_id,
            "TEST_EVENT",
        ) == second_offset

    asyncio.run(run())
