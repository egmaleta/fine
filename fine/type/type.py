from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .kind import Kind, apply
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
        return apply(self.f.kind, [arg.kind for arg in self.args])


@dataclass
class QuantifiedType(Type):
    quantified: set[str]
    inner: Type

    @property
    def kind(self):
        return self.inner.kind
