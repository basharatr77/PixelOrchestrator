import asyncio

from app.core.event_bus import StreamBus
from app.core.events import Event


def test_device_connected_event_reaches_subscriber():
    async def run():
        bus = StreamBus()
        received = []

        def handler(event, offset, group_id):
            received.append(
                (event, offset, group_id)
            )

        bus.subscribe(
            "device-agent",
            "DEVICE_CONNECTED",
            handler,
        )

        event = Event(
            "DEVICE_CONNECTED",
            {
                "serial": "PIXEL_8",
                "mode": "ADB",
            },
        )

        await bus.publish(event)

        queued_offset, queued_event = await bus.queue.get()

        await bus.dispatch(
            queued_offset,
            queued_event,
        )

        assert len(received) == 1

        received_event, received_offset, received_group = received[0]

        assert received_event.type == "DEVICE_CONNECTED"
        assert received_event.payload == {
            "serial": "PIXEL_8",
            "mode": "ADB",
        }
        assert received_offset == queued_offset
        assert received_group == "device-agent"

    asyncio.run(run())
