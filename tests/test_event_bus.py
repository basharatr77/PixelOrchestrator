import asyncio

from core.event_store import EventStore
from core.event_bus import EventBus


def test_basic_publish():
    async def run():
        store = EventStore()
        bus = EventBus(store)

        received = []

        async def handler(data):
            received.append(data)

        bus.subscribe("event.test", handler)

        await bus.publish(
            "event.test",
            {"value": 123},
            persist=False
        )

        assert received == [{"value": 123}]

    asyncio.run(run())


def test_multi_subscriber():
    async def run():
        store = EventStore()
        bus = EventBus(store)

        received = []

        async def handler_a(data):
            received.append("A")

        async def handler_b(data):
            received.append("B")

        async def handler_c(data):
            received.append("C")

        bus.subscribe("event.test", handler_a)
        bus.subscribe("event.test", handler_b)
        bus.subscribe("event.test", handler_c)

        await bus.publish(
            "event.test",
            {"test": "parallel"},
            persist=False
        )

        assert received == ["A", "B", "C"]

    asyncio.run(run())


def test_nested_event_dispatch():
    async def run():
        store = EventStore()
        bus = EventBus(store)

        received = []

        async def handler_a(data):
            received.append(("A", data))

            await bus.publish(
                "event.b",
                {"from": "A"},
                persist=False
            )

        async def handler_b(data):
            received.append(("B", data))

        bus.subscribe("event.a", handler_a)
        bus.subscribe("event.b", handler_b)

        await bus.publish(
            "event.a",
            {"test": "nested"},
            persist=False
        )

        assert received == [
            ("A", {"test": "nested"}),
            ("B", {"from": "A"}),
        ]

    asyncio.run(run())


def test_dedup_loop_protection():
    async def run():
        store = EventStore()
        bus = EventBus(store)

        received = []

        async def handler_a(data):
            received.append("A")

            if len(received) < 10:
                await bus.publish(
                    "event.b",
                    {"loop": "test"},
                    persist=False
                )

        async def handler_b(data):
            received.append("B")

            if len(received) < 10:
                await bus.publish(
                    "event.a",
                    {"loop": "test"},
                    persist=False
                )

        bus.subscribe("event.a", handler_a)
        bus.subscribe("event.b", handler_b)

        await bus.publish(
            "event.a",
            {"loop": "test"},
            persist=False
        )

        assert received == ["A", "B"]

    asyncio.run(run())
