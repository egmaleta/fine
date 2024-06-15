from dataclasses import dataclass

from ..utils import String, Env


class Kind:
    pass


@dataclass
class AtomKind(Kind):
    def __repr__(self):
        return "*"


ATOM_KIND = AtomKind()


@dataclass
class FunctionKind(Kind):
    args: list[Kind]

    def __post_init__(self):
        assert len(self.args) >= 2

    @property
    def left(self):
        return self.args[0]

    @property
    def right(self):
        match self.args[1:]:
            case [kind]:
                return kind
            case kinds:
                return FunctionKind(kinds)

    def __repr__(self):
        return " -> ".join(
            f"({kind})" if isinstance(kind, FunctionKind) else repr(kind)
            for kind in self.args
        )


type KindEnv = Env[Kind | None]


class _Kinded:
    _kind: Kind | None = None


class Type:
    def __len__(self):
        return 1


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


def check_kind(type: Type, expected_kind: Kind):
    """
    Kind checker function.

    Must be used after kind inference of 'type'.
    """

    match type:
        case TypeConstant() | TypeVar():
            assert type._kind == expected_kind

        case TypeApp(f, args):
            fkind = f._kind

            for type_arg in args:
                assert isinstance(fkind, FunctionKind)
                check_kind(type_arg, fkind.left)
                fkind = fkind.right

            assert fkind == expected_kind

        case FunctionType() as ftype:
            check_kind(ftype.left, ATOM_KIND)
            check_kind(ftype.right, ATOM_KIND)

        case TypeScheme(_, inner):
            return check_kind(inner, expected_kind)


def kindof(type: Type) -> Kind:
    """
    Kind getter function.

    Must be used after kind inference and kind checking of 'type'.
    """

    match type:
        case TypeConstant() | TypeVar():
            assert type._kind is not None
            return type._kind

        case TypeApp(f, args):
            fkind = f._kind
            assert isinstance(fkind, FunctionKind)

            match fkind.args[len(args) :]:
                case [kind]:
                    return kind
                case kinds:
                    return FunctionKind(kinds)

        case FunctionType():
            return ATOM_KIND

        case TypeScheme(_, inner):
            return kindof(inner)
