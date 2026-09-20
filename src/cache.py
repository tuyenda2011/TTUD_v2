"""Bounded FIFO caches: eviction changes speed, never solution semantics."""
class BoundedCache(dict):
    def __init__(self, limit=10000):
        super().__init__()
        self.limit = limit

    def __setitem__(self, key, value):
        if self.limit and key not in self and len(self) >= self.limit:
            del self[next(iter(self))]
        super().__setitem__(key, value)
