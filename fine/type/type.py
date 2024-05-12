from dataclasses import dataclass, field

from .kind import Kind


@dataclass
class Type:
    kind: Kind | None = field(init=False, default=None)


@dataclass
class NamedType(Type):
    name: str


class TypeConstant(NamedType):
    pass


class TypeVar(NamedType):
    pass


@dataclass
class TypeApp(Type):
    f: TypeConstant | TypeVar
    args: list[Type]


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
