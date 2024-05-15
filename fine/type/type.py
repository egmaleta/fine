from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .kind import Kind, apply


class Type(ABC):
    @property
    @abstractmethod
    def kind(self) -> Kind:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


@dataclass
class AtomType:
    _name: str
    _kind: Kind | None = field(default=None)

    @property
    def kind(self):
        assert self._kind is not None
        return self._kind

    @property
    def name(self):
        return self._name

    def set_kind(self, kind: Kind):
        assert self._kind is None
        self._kind = kind


class TypeConstant(AtomType):
    pass


class TypeVar(AtomType):
    pass


@dataclass
class TypeApp(Type):
    f: TypeConstant | TypeVar
    args: list[Type]

    @property
    def kind(self):
        return apply(self.f.kind, [arg.kind for arg in self.args])

    @property
    def name(self):
        return self.f.name


@dataclass
class FunctionType(TypeApp):
    def __post_init__(self):
        assert len(self.args) == 2

    @property
    def left(self):
        return self.args[0]

    @property
    def right(self):
        return self.args[1]


@dataclass
class QuantifiedType(Type):
    quantified: set[str]
    type: Type

    @property
    def kind(self):
        return self.type.kind

    @property
    def name(self):
        return self.type.name
