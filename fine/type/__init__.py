from dataclasses import dataclass

from ..utils import String, raw_str
from .kind import Kind, FunctionKind, ATOM_KIND


type Type = (
    TypeConstant | TypeVar | TypeApp[Type, Type] | FunctionType[Type] | TypeScheme[Type]
)


class _Kinded:
    _kind: Kind | None = None


@dataclass
class TypeConstant(_Kinded):
    name: String

    def __len__(self):
        return 1

    def __repr__(self):
        return raw_str(self.name)


@dataclass
class TypeVar(_Kinded):
    name: String

    def __len__(self):
        return 1

    def __repr__(self):
        return raw_str(self.name)


@dataclass
class TypeApp[T: TypeConstant | TypeVar, A: Type]:
    f: T
    args: list[A]

    @property
    def name(self):
        return self.f.name

    def __len__(self):
        return 1

    def __repr__(self):
        args_repr = ", ".join(repr(targ) for targ in self.args)
        return f"{self.f}({args_repr})"


@dataclass
class FunctionType[T: Type]:
    args: list[T]

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

    def __repr__(self):
        return " -> ".join(
            f"({targ})" if isinstance(targ, FunctionType) else repr(targ)
            for targ in self.args
        )


@dataclass
class TypeScheme[T: Type]:
    vars: set[String]
    type: T

    def __post_init__(self):
        if isinstance(self.vars, list):
            self.vars = set(self.vars)

    def __len__(self):
        return len(self.type)

    def __repr__(self):
        vars = " ".join(raw_str(var) for var in self.vars)
        return f"forall {vars}. {self.type}"


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

        case FunctionType():
            return ATOM_KIND

        case TypeScheme(_, inner):
            return kindof(inner)


def clone[T: Type](type: T) -> T:
    match type:
        case TypeConstant(name):
            return TypeConstant(name)

        case TypeVar(name):
            return TypeVar(name)

        case TypeApp(f, args):
            return TypeApp(clone(f), [clone(targ) for targ in args])

        case FunctionType(args):
            return FunctionType([clone(targ) for targ in args])

        case TypeScheme(vars, inner):
            return TypeScheme({*vars}, clone(inner))
