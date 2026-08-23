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
