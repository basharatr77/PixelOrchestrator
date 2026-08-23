import asyncio

from app.core.bus_runtime import BusRuntime


def test_bus_runtime_run_starts_execution_task_and_can_be_cancelled():
    async def run():
        runtime = BusRuntime()

        task = asyncio.create_task(runtime.run())

        for _ in range(100):
            if runtime.execution_task is not None:
                break
            await asyncio.sleep(0.01)

        assert runtime.execution_task is not None
        assert not runtime.execution_task.done()
        assert runtime.pool.tasks

        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert runtime.execution_task.done()

        await runtime.pool.stop()

    asyncio.run(run())
