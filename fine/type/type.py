from dataclasses import dataclass

from ..utils import String

from . import kind as k


class Type:
    pass


class _Kinded:
    _kind: k.Kind | None = None


@dataclass
class TypeConstant(Type, _Kinded):
    name: String


@dataclass
class TypeVar(Type, _Kinded):
    name: String


@dataclass
class TypeApp(Type):
    f: TypeConstant | TypeVar
    args: list[Type]

    @property
    def name(self):
        return self.f.name


@dataclass
class TypeScheme(Type):
    vars: set[String]
    type: Type

    def __post_init__(self):
        if isinstance(self.vars, list):
            self.vars = set(self.vars)

    def __len__(self):
        return len(self.type)


def kindof(type: Type) -> k.Kind:
    match type:
        case TypeConstant() | TypeVar():
            assert type._kind is not None
            return type._kind

        case TypeApp(f, args):
            kind = kindof(f)
            for _ in args:
                assert isinstance(kind, k.FunctionKind)
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
