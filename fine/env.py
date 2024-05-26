from typing import Self


class Env[V]:
    def __init__(self, parent: Self | None = None):
        self._values: dict[str, V] = {}
        self._parent = parent

    def _search(self, key: str, local: bool):
        if key in self._values:
            return self._values

        if not local and self._parent is not None:
            return self._parent._search(key, local)

        return None

    def get(self, key: str, local=False) -> tuple[V, bool]:
        values = self._search(key, local)

        if values is not None:
            return values[key], True

        return None, False

    def set(self, key: str, value: V, local=True, override=False):
        values = self._search(key, local)
        found = values is not None

        if found and override:
            values[key] = value
        elif not found:
            self._values[key] = value

    def child_env(self):
        return Env(self)
