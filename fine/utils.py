from typing import Self


class Scope[K, V]:
    def __init__(self, parent: Self | None = None):
        self._values: dict[K, V] = {}
        self._parent = parent

    def new_scope(self):
        return Scope(self)

    def get(self, key: K, local=False) -> V | None:
        value = self._values.get(key)
        if value is not None:
            return value

        if not local and self._parent is not None:
            return self._parent.get(key, local)

        return None

    def has(self, key: K, local=False):
        return self.get(key, local) is not None

    def add(self, key: K, value: V):
        if not self.has(key, True):
            self._values[key] = value
            return True

        return False
