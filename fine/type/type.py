from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .kind import Kind, apply


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
    name: str


@dataclass
class TypeVar(AtomType):
    name: str


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
