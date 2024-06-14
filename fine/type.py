from dataclasses import dataclass, field

from .utils import String, Env


class Kind:
    pass


@dataclass
class AtomKind(Kind):
    def __repr__(self):
        return "Type"


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


class Quantifier:
    @staticmethod
    def _format_vars(vars):
        match [*vars]:
            case [var]:
                return f"Type variable '{var}' is"
            case [*leading, last]:
                leading = ", ".join(f"'{v}'" for v in leading)
                return f"Type variables {leading} and '{last}' are"

    @staticmethod
    def _assert_unused(vars: set[String]):
        assert len(vars) == 0, f"{Quantifier._format_vars(vars)} unused."

    @staticmethod
    def _assert_free(vars: set[String]):
        assert len(vars) == 0, f"{Quantifier._format_vars(vars)} free."

    def _quantify(self, type: Type):
        match type:
            case TypeConstant():
                return set()

            case TypeVar(name):
                return {name}

            case TypeApp(f, args):
                vars = self._quantify(f)
                for type in args:
                    vars |= self._quantify(type)
                return vars

            case FunctionType(args):
                vars = set()
                for type in args:
                    vars |= self._quantify(type)
                return vars

            case TypeScheme(vars, inner):
                captured = self._quantify(inner)

                self._assert_unused(vars - captured)

                free = captured - vars
                return free

    def quantify(self, type: Type):
        free = self._quantify(type)

        if not isinstance(type, TypeScheme):
            return TypeScheme(free, type) if len(free) > 0 else type

        self._assert_free(free)

        return type


class KindInferer:
    def _assign(self, type: Type, kind: Kind, setter_env: KindEnv):
        match type:
            case TypeConstant(name) | TypeVar(name):
                type._kind = kind
                # make it available
                assert setter_env.set(name, kind)

            case TypeScheme(_, inner):
                self._assign(inner, kind, setter_env)

            case _:
                assert False

    def _infer(self, type: Type, env: KindEnv) -> tuple[Kind | None, KindEnv]:
        match type:
            case TypeConstant(name) | TypeVar(name):
                kind, found = env.get(name)
                assert found

                # a kind might be available for this type
                if kind is not None and type._kind is None:
                    type._kind = kind

                return type._kind, env

            case TypeApp(f, args):
                fkind, fsetter_env = self._infer(f, env)

                # kind(f) == kind(arg1) -> kind(arg2) -> ... -> *
                if fkind is None:
                    kinds = []
                    for type_arg in args:
                        kind, _ = self._infer(type_arg, env)
                        if kind is None:
                            break
                        kinds.append(kind)
                    else:
                        self._assign(f, FunctionKind([*kinds, ATOM_KIND]), fsetter_env)
                else:
                    for type_arg in args:
                        assert isinstance(fkind, FunctionKind)
                        lkind = fkind.left

                        kind, setter_env = self._infer(type_arg, env)
                        if kind is None:
                            self._assign(type_arg, lkind, setter_env)

                        fkind = fkind.right

                return ATOM_KIND, env

            case FunctionType() as ftype:
                # kind(->) == * -> *
                for type_arg in [ftype.left, ftype.right]:
                    kind, setter_env = self._infer(type_arg, env)
                    if kind is None:
                        self._assign(type_arg, ATOM_KIND, setter_env)

                return ATOM_KIND, env

            case TypeScheme(vars, inner):
                child_env = env.child_env()
                for name in vars:
                    child_env.add(name, None)

                return self._infer(inner, child_env)

    def infer(self, type: Type, env: KindEnv):
        kind, setter_env = self._infer(type, env)
        if kind is None:
            self._assign(kind, ATOM_KIND, setter_env)
            return ATOM_KIND

        return kind


def check_kind(type: Type, expected_kind=ATOM_KIND):
    match type:
        case TypeConstant() | TypeVar():
            assert type._kind == expected_kind

        case TypeApp(f, args):
            fkind = kindof(f)

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
    match type:
        case TypeConstant() | TypeVar():
            assert type._kind is not None
            return type._kind

        case TypeApp(f, args):
            fkind = kindof(f)
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
