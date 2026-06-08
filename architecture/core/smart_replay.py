from architecture.storage.wal_store import WALStore

class SmartReplay:
    def __init__(self, wal):
        self.wal = wal

    def replay(self, handler, since_ts=0):
        for event in self.wal.load():
            if event["_ts"] >= since_ts:
                handler(event)
