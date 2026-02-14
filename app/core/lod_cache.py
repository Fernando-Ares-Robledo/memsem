"""Simple LOD image cache."""

from __future__ import annotations

from collections import OrderedDict


class LODCache:
    def __init__(self, max_items: int = 2048):
        self.max_items = max_items
        self._store: OrderedDict[tuple, object] = OrderedDict()

    def get(self, key):
        value = self._store.get(key)
        if value is not None:
            self._store.move_to_end(key)
        return value

    def put(self, key, value):
        self._store[key] = value
        self._store.move_to_end(key)
        while len(self._store) > self.max_items:
            self._store.popitem(last=False)

    def clear(self):
        self._store.clear()
