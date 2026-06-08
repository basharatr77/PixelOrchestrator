from collections import defaultdict

class ConsumerGroup:
    def __init__(self):
        self.groups = defaultdict(list)
        self.assignment = {}

    def add(self, group, consumer_id):
        if consumer_id not in self.groups[group]:
            self.groups[group].append(consumer_id)

    def assign(self, group, partitions):
        consumers = self.groups[group]

        if not consumers:
            return {}

        mapping = {}

        for i, p in enumerate(partitions):
            cid = consumers[i % len(consumers)]
            mapping[p] = cid

        self.assignment[group] = mapping
        return mapping

    def owner(self, group, partition):
        return self.assignment.get(group, {}).get(partition)
