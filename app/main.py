import asyncio

from app.core.bus_runtime import BusRuntime
from app.dashboard.ws_server import run_dashboard


async def main():
    runtime = BusRuntime()

    runtime_task = asyncio.create_task(runtime.run())
    dashboard_task = asyncio.create_task(run_dashboard(runtime.bus))

    done, pending = await asyncio.wait(
        {runtime_task, dashboard_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()

    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    for task in done:
        task.result()


if __name__ == "__main__":
    asyncio.run(main())
