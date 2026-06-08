import asyncio
from app.core.events import Event
from app.core.kafka.bus import KafkaBus

async def main():
    bus = KafkaBus()

    async def handler(event, pid, offset):
        print(f"[P{pid}:{offset}] {event.type} -> {event.payload}")

    bus.subscribe("group-a", handler)
    bus.subscribe("group-b", handler)

    # publish + dispatch immediately
    for payload in [{"id": "pixel-1"}, {"id": "pixel-2"}]:
        event = Event("device_connected", payload)

        pid, offset = await bus.publish(event)

        # IMPORTANT: trigger dispatch
        await bus.dispatch(event, pid, offset)

if __name__ == "__main__":
    asyncio.run(main())
