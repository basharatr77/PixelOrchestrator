class CommitTracker:
    def __init__(self):
        self.commit_index = -1
        self.applied_index = -1

    def commit(self, index):
        self.commit_index = index

    def safe_to_apply(self, index):
        return index <= self.commit_index
