from dataclasses import dataclass

from ..utils import String

from .kind import Kind, FunctionKind


type Type = TypeConstant | TypeVar | TypeApp | FunctionType | TypeScheme


class _Kinded:
    _kind: Kind | None = None


@dataclass
class TypeConstant(_Kinded):
    name: String


@dataclass
class TypeVar(_Kinded):
    name: String


@dataclass
class TypeApp:
    f: TypeConstant | TypeVar
    args: list[Type]

    @property
    def name(self):
        return self.f.name


@dataclass
class FunctionType:
    args: list[Type]

    def __post_init__(self):
        assert len(self.args) >= 2

    @property
    def left(self):
        return self.args[0]

    @property
    def right(self):
        match self.args[1:]:
            case [type]:
                return type
            case types:
                return FunctionType(types)

    def __len__(self):
        return len(self.args)


@dataclass
class TypeScheme:
    vars: set[String]
    type: Type

    def __post_init__(self):
        if isinstance(self.vars, list):
            self.vars = set(self.vars)

    def __len__(self):
        return len(self.type)


def kindof(type: Type) -> Kind:
    match type:
        case TypeConstant() | TypeVar():
            assert type._kind is not None
            return type._kind

        case TypeApp(f, args):
            kind = kindof(f)
            for _ in args:
                assert isinstance(kind, FunctionKind)
                kind = kind.right

            return kind

        case TypeScheme(_, inner):
            return kindof(inner)


def ftype_length(type: Type) -> int:
    match type:
        case TypeApp(f, args):
            if f.name == "->" and len(args) == 2:
                return 1 + ftype_length(args[1])

        case TypeScheme(_, inner):
            return ftype_length(inner)

    return 1
