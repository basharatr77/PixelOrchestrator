class RaftLog:
    def __init__(self):
        self.entries = []
        self.commit_index = -1

    def append(self, entry):
        self.entries.append(entry)
        return len(self.entries) - 1

    def get_from(self, index):
        return self.entries[index:]
