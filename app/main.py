import asyncio

from app.core.bus_runtime import BusRuntime
from app.dashboard.ws_server import run_dashboard


async def main():
    runtime = BusRuntime()

    await asyncio.gather(
        runtime.run(),
        run_dashboard(runtime.bus),
    )


if __name__ == "__main__":
    asyncio.run(main())
