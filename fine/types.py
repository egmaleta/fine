from dataclasses import dataclass
from abc import abstractmethod, ABC


@dataclass
class Type(ABC):
    name: str

    @property
    @abstractmethod
    def is_concrete(self) -> bool:
        pass

    def __eq__(self, other):
        return isinstance(other, type(self)) and other.name == self.name


class ConcreteType(Type):
    @property
    def is_concrete(self):
        return True


class TypeVar(Type):
    @property
    def is_concrete(self):
        return False


@dataclass
class PolyType(Type):
    args: list[Type]

    @property
    def is_concrete(self) -> bool:
        return all(a.is_concrete for a in self.args)

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        if len(self.args) != len(other.args):
            return False

        return all(x == y for x, y in zip(self.args, other.args))
