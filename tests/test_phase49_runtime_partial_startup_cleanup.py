import asyncio

import pytest

from app.core import bus_runtime as runtime_module
from app.core.worker_pool import WorkerPool


def test_runtime_cleans_up_started_tasks_when_later_startup_fails(monkeypatch):
    async def scenario():
        class FakeBus:
            def __init__(self):
                self.queue = asyncio.Queue()

        runtime = object.__new__(runtime_module.BusRuntime)
        runtime.setup = lambda: None
        runtime.pool = WorkerPool(FakeBus())

        async def wait_forever():
            await asyncio.Future()

        runtime.execution_loop = wait_forever
        runtime.detector_loop = wait_forever
        runtime.execution_task = None
        runtime.detector_task = None

        original_create_task = runtime_module.asyncio.create_task
        created_tasks = []

        def fail_detector_task(coroutine):
            if len(created_tasks) == 4:
                coroutine.close()
                raise RuntimeError("detector task startup failed")

            task = original_create_task(coroutine)
            created_tasks.append(task)
            return task

        monkeypatch.setattr(
            runtime_module.asyncio,
            "create_task",
            fail_detector_task,
        )

        try:
            with pytest.raises(
                RuntimeError,
                match="detector task startup failed",
            ):
                await runtime.run()

            assert runtime.execution_task.done()
            assert runtime.pool.tasks == []
        finally:
            if runtime.execution_task is not None and not runtime.execution_task.done():
                runtime.execution_task.cancel()
            await runtime.pool.stop()
            if runtime.execution_task is not None:
                await asyncio.gather(
                    runtime.execution_task,
                    return_exceptions=True,
                )

    asyncio.run(scenario())
