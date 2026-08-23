import asyncio

from app.core.events import Event
from app.core.event_bus import StreamBus
from app.core.worker_pool import WorkerPool


def test_worker_pool_stop_cleans_up_workers_and_completes_queue():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=2)

        handled = []

        def handler(event, offset, group_id):
            handled.append(event.type)

        bus.subscribe(
            "test",
            "TEST_EVENT",
            handler,
        )

        await bus.publish(
            Event(
                "TEST_EVENT",
                {"value": 1},
            )
        )

        await pool.start()

        await asyncio.wait_for(
            bus.queue.join(),
            timeout=1.0,
        )

        assert handled == ["TEST_EVENT"]

        await pool.stop()

        assert pool.tasks == []

    asyncio.run(run())

def test_worker_pool_start_is_idempotent():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=3)

        await pool.start()
        first_tasks = list(pool.tasks)

        await pool.start()

        assert len(pool.tasks) == 3
        assert pool.tasks == first_tasks

        await pool.stop()

    asyncio.run(run())


def test_worker_pool_stop_is_idempotent():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=2)

        await pool.start()
        await pool.stop()

        assert pool.tasks == []

        await pool.stop()

        assert pool.tasks == []

    asyncio.run(run())


def test_worker_pool_marks_queue_done_when_handler_fails():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=1)

        def failing_handler(event, offset, group_id):
            raise RuntimeError("handler failure")

        bus.subscribe(
            "test",
            "TEST_EVENT",
            failing_handler,
        )

        await bus.publish(
            Event(
                "TEST_EVENT",
                {"value": 1},
            )
        )

        await pool.start()

        await asyncio.wait_for(
            bus.queue.join(),
            timeout=1.0,
        )

        await pool.stop()

    asyncio.run(run())
