import asyncio
from architecture.core.partition_router import PartitionRouter
from architecture.core.event_bus import EventBus

class RoutedBus:
    def __init__(self):
        self.router = PartitionRouter()
        self.bus = EventBus()

    def subscribe(self, group, handler):
        self.bus.subscribe(group, handler)

    async def publish(self, topic, event):
        partition = self.router.route(event["id"])
        event["_partition"] = partition
        await self.bus.publish(topic, event)
