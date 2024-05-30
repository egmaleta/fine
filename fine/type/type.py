from dataclasses import dataclass

from ..utils import String


class Type:
    def __len__(self):
        return 1


@dataclass
class TypeConstant(Type):
    name: String


@dataclass
class TypeVar(Type):
    name: String


@dataclass
class TypeApp(Type):
    fname: String
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

    def __len__(self):
        return len(self.inner_type)
