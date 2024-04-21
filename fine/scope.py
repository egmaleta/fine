from typing import Self


class Scope[T]:
    def __init__(self, parent: Self | None = None):
        self._store: dict[str, T] = {}
        self._parent = parent

    def new_child(self):
        return Scope[T](self)

    def top_scope(self) -> Self:
        if self._parent is None:
            return self
        return self._parent.top_scope()

    def get_item(self, name: str, *, local=False) -> T | None:
        item = self._store.get(name)
        if item is not None:
            return item

        if not local and self._parent is not None:
            return self._parent.get_item(name, local=local)

        return None

    def has_item(self, name: str, *, local=False):
        return self.get_item(name, local=local) is not None

    def add_item(self, name: str, item: T):
        if not self.has_item(name, local=True):
            self._store[name] = item
            return True

        return False
