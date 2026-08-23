import asyncio

from app.core.event_bus import StreamBus
from app.core.events import Event
from app.core.worker_pool import WorkerPool


def test_worker_survives_dispatch_exception_and_processes_next_event():
    async def run():
        bus = StreamBus()
        pool = WorkerPool(bus, worker_count=1)

        handled = []
        dispatch_calls = {"value": 0}

        original_dispatch = bus.dispatch

        async def flaky_dispatch(offset, event):
            dispatch_calls["value"] += 1

            if dispatch_calls["value"] == 1:
                raise RuntimeError("dispatch failure")

            await original_dispatch(offset, event)

        bus.dispatch = flaky_dispatch

        def handler(event, offset, group_id):
            handled.append(event.payload["value"])

        bus.subscribe(
            "worker-dispatch-failure-test",
            "TEST_EVENT",
            handler,
        )

        await bus.publish(
            Event(
                "TEST_EVENT",
                {"value": 1},
            )
        )

        await bus.publish(
            Event(
                "TEST_EVENT",
                {"value": 2},
            )
        )

        await pool.start()

        await asyncio.wait_for(
            bus.queue.join(),
            timeout=2.0,
        )

        assert handled == [2]

        assert len(pool.tasks) == 1
        assert not pool.tasks[0].done()

        await pool.stop()

        assert pool.tasks == []

    asyncio.run(run())
