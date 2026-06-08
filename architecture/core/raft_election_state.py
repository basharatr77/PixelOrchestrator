class RaftElectionState:
    def __init__(self):
        self.current_term = 0
        self.leader = None
        self.voted_for = None

    def set_leader(self, leader):
        self.leader = leader

    def is_leader(self, node):
        return self.leader == node
