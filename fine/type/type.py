from dataclasses import dataclass, field

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

    _env: KindEnv | None = field(init=False, compare=False, repr=False, default=None)

    def __post_init__(self):
        if isinstance(self.vars, list):
            self.vars = set(self.vars)

    def __len__(self):
        return len(self.type)


def check_kind(type: Type, expected_kind: Kind, env: KindEnv):
    """
    Kind checker function.

    Must be used after kind inference of 'type'.
    """

    match type:
        case TypeConstant(name) | TypeVar(name):
            kind, found = env.get(name)
            assert found
            assert kind == expected_kind

        case TypeApp(f, args):
            fkind = kindof(f, env)

            for type_arg in args:
                assert isinstance(fkind, FunctionKind)
                check_kind(type_arg, fkind.left, env)
                fkind = fkind.right

            assert fkind == expected_kind

        case FunctionType() as ftype:
            check_kind(ftype.left, ATOM_KIND, env)
            check_kind(ftype.right, ATOM_KIND, env)

        case TypeScheme(_, inner):
            assert type._env is not None
            return check_kind(inner, expected_kind, type._env)


def kindof(type: Type, env: KindEnv) -> Kind:
    """
    Kind getter function.

    Must be used after kind inference and kind checking of 'type'.
    """

    match type:
        case TypeConstant(name) | TypeVar(name):
            kind, found = env.get(name)
            assert found
            assert kind is not None

            return kind

        case TypeApp(f, args):
            fkind = kindof(f, env)
            assert isinstance(fkind, FunctionKind)

            match fkind.args[len(args) :]:
                case [kind]:
                    return kind
                case kinds:
                    return FunctionKind(kinds)

        case FunctionType():
            return ATOM_KIND

        case TypeScheme(_, inner):
            assert type._env is not None
            return kindof(inner, type._env)
