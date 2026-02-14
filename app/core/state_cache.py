from __future__ import annotations

from collections import OrderedDict


class LRUCache:
    def __init__(self, max_items: int = 64):
        self.max_items = max_items
        self._store: OrderedDict[str, object] = OrderedDict()

    def get(self, key: str):
        if key not in self._store:
            return None
        val = self._store.pop(key)
        self._store[key] = val
        return val

    def put(self, key: str, value: object) -> None:
        if key in self._store:
            self._store.pop(key)
        self._store[key] = value
        if len(self._store) > self.max_items:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()
