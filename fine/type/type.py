from dataclasses import dataclass
from lark.lexer import Token


class Type:
    pass


@dataclass
class TypeConstant(Type):
    name: Token


@dataclass
class TypeVar(Type):
    name: Token


@dataclass
class TypeApp(Type):
    fname: Token
    args: list[Type]


@dataclass
class FunctionType(Type):
    inner_types: list[Type]

    def __post_init__(self):
        assert len(self.inner_types) >= 2

    @property
    def left(self):
        return self.inner_types[0]

    @property
    def right(self):
        match self.inner_types[1:]:
            case [type]:
                return type
            case types:
                return FunctionType(types)

    def __len__(self):
        return len(self.inner_types)


@dataclass
class QuantifiedType(Type):
    quantified: set[str]
    inner_type: Type

    def __post_init__(self):
        if isinstance(self.quantified, list):
            self.quantified = set(self.quantified)
