from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import ClassVar

from .kind import Kind, FunctionKind
from ..utils import String


class Type(ABC):
    @property
    @abstractmethod
    def kind(self) -> Kind:
        pass


@dataclass
class AtomType(Type):
    _kind: Kind | None = field(init=False, default=None)

    @property
    def kind(self):
        assert self._kind is not None
        return self._kind

    @kind.setter
    def kind(self, kind: Kind):
        assert self._kind is None
        self._kind = kind


@dataclass
class TypeConstant(AtomType):
    name: String


@dataclass
class TypeVar(AtomType):
    name: String


@dataclass
class TypeApp(Type):
    f: TypeConstant | TypeVar
    args: list[Type]

    @property
    def kind(self):
        k = self.f.kind
        for arg in self.args:
            assert isinstance(k, FunctionKind)
            assert k.left == arg.kind
            k = k.right

        return k


@dataclass
class FunctionType(TypeApp):
    NAME: ClassVar[str] = "->"

    def __post_init__(self):
        assert isinstance(self.f, TypeConstant)
        assert self.f.name == self.NAME
        assert len(self.args) == 2

    @property
    def left(self):
        return self.args[0]

    @property
    def right(self):
        return self.args[1]

    def __len__(self):
        l = len(self.right) if isinstance(self.right, FunctionType) else 1
        return 1 + l


@dataclass
class QuantifiedType(Type):
    quantified: set[str]
    inner: Type

    @property
    def kind(self):
        return self.inner.kind
