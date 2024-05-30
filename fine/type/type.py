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
    ftype_name: String
    type_args: list[Type]


@dataclass
class FunctionType(Type):
    type_args: list[Type]

    def __post_init__(self):
        assert len(self.type_args) >= 2

    @property
    def left(self):
        return self.type_args[0]

    @property
    def right(self):
        match self.type_args[1:]:
            case [type]:
                return type
            case types:
                return FunctionType(types)

    def __len__(self):
        return len(self.type_args)


@dataclass
class QuantifiedType(Type):
    vars: set[str]
    inner_type: Type

    def __post_init__(self):
        if isinstance(self.vars, list):
            self.vars = set(self.vars)

    def __len__(self):
        return len(self.inner_type)
