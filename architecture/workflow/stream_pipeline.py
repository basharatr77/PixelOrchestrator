import asyncio
from architecture.core.stream_processor import StreamProcessor

stream = StreamProcessor()

async def handler(event):
    print("PROCESSING:", event)

async def main():
    stream.subscribe("DEVICE_DETECTED", handler)

    asyncio.create_task(stream.start())

    stream.publish("DEVICE_DETECTED", {
        "type": "DEVICE_DETECTED",
        "data": {"id": "pixel-1"}
    })

    await asyncio.sleep(2)

asyncio.run(main())
