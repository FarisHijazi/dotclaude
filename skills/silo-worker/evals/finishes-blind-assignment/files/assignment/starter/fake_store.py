class FakeStore:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return list(self.data.get(key, []))

    def put(self, key, values):
        self.data[key] = list(values)
