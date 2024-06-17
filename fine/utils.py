from typing import Self
from lark.lexer import Token


type String = str | Token


class Env[V]:
    def __init__(self, parent: Self | None = None):
        self._values: dict[String, V] = {}
        self._parent = parent

    def _search(self, key: String, local: bool) -> dict[String, V] | None:
        if key in self._values:
            return self._values

        if not local and self._parent is not None:
            return self._parent._search(key, local)

        return None

    def get(self, key: String, *, local=False) -> tuple[V, bool]:
        values = self._search(key, local)

        if values is not None:
            return values[key], True

        return None, False

    def set(self, key: String, value: V, *, local=False):
        values = self._search(key, local)

        if values is not None:
            values[key] = value
            return True

        return False

    def add(self, key: String, value: V):
        if key not in self._values:
            self._values[key] = value
            return True

        return False

    def child(self):
        return Env(self)

    def __iter__(self):
        for key, value in self._values.items():
            yield key, value
