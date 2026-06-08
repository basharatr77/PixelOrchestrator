class ReplayEngine:

    def __init__(self, store, bus):
        self.store = store
        self.bus = bus

    async def replay(self):

        print("[REPLAY] Loading historical events...")

        events = self.store.load_events()

        print(f"[REPLAY] {len(events)} events found")

        for event in events:

            # ✅ IMPORTANT: mark replay mode so AI doesn't re-trigger loops
            if hasattr(event, "get"):
                event_type = event.get("type")
                data = event.get("data")
            else:
                continue

            # ❌ DO NOT re-store replay events again
            await self.bus.publish(event_type, data)
