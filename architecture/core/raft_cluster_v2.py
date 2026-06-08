import time
import random
from architecture.core.raft_state import RaftState

class RaftClusterV2:
    def __init__(self, nodes):
        self.nodes = nodes
        self.state = {}
        self.leader = None
        self.term = 0

        for n in nodes:
            self.state[n] = RaftState.FOLLOWER

    def elect(self):
        self.term += 1

        votes = {}
        for n in self.nodes:
            votes[n] = random.choice([True, True, False])  # quorum bias

        winners = [n for n, v in votes.items() if v]

        if len(winners) >= (len(self.nodes)//2 + 1):
            self.leader = winners[0]
            self.state[self.leader] = RaftState.LEADER
            return self.leader

        return None
