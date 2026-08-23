import asyncio

from app.core.bus_runtime import BusRuntime


async def main():
    runtime = BusRuntime()
    await runtime.run()


if __name__ == "__main__":
    asyncio.run(main())
