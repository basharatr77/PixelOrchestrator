class AutoRebalancer:
    def __init__(self, broker, control_plane):
        self.broker = broker
        self.cp = control_plane

    def rebalance(self, group_id):
        active = self.cp.get_active_consumers()

        if not active:
            print("[REBALANCE] No active consumers")
            return

        self.broker.assignment = {}

        for i, consumer_id in enumerate(active):
            self.broker.assignment[(group_id, i)] = {
                "id": consumer_id
            }

        print("[REBALANCE] New assignment:", self.broker.assignment)
