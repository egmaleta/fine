from dataclasses import dataclass

from ..utils import String

from . import kind as k


class Type:
    def __len__(self):
        return 1


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
class FunctionType(Type):
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

        case FunctionType():
            return k.ATOM_KIND

        case TypeScheme(_, inner):
            return kindof(inner)
