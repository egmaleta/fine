from abc import abstractmethod
from dataclasses import dataclass

from .base import String, AST


class Type(AST):
    @property
    @abstractmethod
    def is_concrete(self) -> bool:
        pass

    def __eq__(self, other):
        return isinstance(other, type(self))


@dataclass
class NamedType(Type):
    name: String

    def __eq__(self, other):
        return super().__eq__(other) and self.name == other.name

    def __len__(self):
        return 1


class ConcreteType(NamedType):
    @property
    def is_concrete(self):
        return True


class TypeVar(NamedType):
    @property
    def is_concrete(self):
        return False


@dataclass
class PolyType(NamedType):
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


@dataclass
class FunctionType(Type):
    left: Type
    right: Type

    @property
    def is_concrete(self):
        return self.left.is_concrete and self.right.is_concrete

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.left == other.left
            and self.right == other.right
        )


INT_TYPE = ConcreteType("Int")
FLOAT_TYPE = ConcreteType("Float")
BOOL_TYPE = ConcreteType("Bool")
UNIT_TYPE = ConcreteType("Unit")
