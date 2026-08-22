import json


class ReplayEngine:

    def __init__(self, store, bus):
        self.store = store
        self.bus = bus

    async def replay(self):

        print("[REPLAY] Loading historical events...")

        events = self.store.get_events()

        print(f"[REPLAY] {len(events)} events found")

        for event in events:
            try:
                _, event_type, payload, _ = event

                data = json.loads(payload)

                await self.bus.publish(
                    event_type,
                    data,
                    persist=False,
                    dedup=False
                )

            except Exception as e:
                print(f"[REPLAY] Event replay failed: {e}")
