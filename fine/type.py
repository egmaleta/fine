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

    @property
    def env(self):
        assert self._env is not None
        return self._env

    @env.setter
    def env(self, new_env: KindEnv):
        assert self._env is None
        self._env = new_env


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
    def _assign(self, type: Type, env: KindEnv, kind: Kind):
        match type:
            case TypeVar(name) | TypeConstant(name):
                assert env.set(name, kind)

            case TypeScheme(_, inner):
                self._assign(inner, env, kind)

            case _:
                assert False

    def _infer(self, type: Type, env: KindEnv):
        match type:
            case TypeConstant(name) | TypeVar(name):
                kind, found = env.get(name)
                assert found

                return kind

            case TypeApp(f, args):
                f_kind = self._infer(f, env)

                if f_kind is not None:
                    for type in args:
                        assert isinstance(f_kind, FunctionKind)
                        left_kind = f_kind.left

                        kind = self._infer(type, env)
                        if kind is not None:
                            assert kind == left_kind
                        else:
                            self._assign(type, env, left_kind)

                        f_kind = f_kind.right

                    return f_kind

                arg_kinds = []
                for type in args:
                    kind = self._infer(type, env)
                    if kind is not None:
                        arg_kinds.append(kind)
                    else:
                        self._assign(type, env, ATOM_KIND)
                        arg_kinds.append(ATOM_KIND)

                assert env.set(f.name, FunctionKind([*arg_kinds, ATOM_KIND]))

                return ATOM_KIND

            case FunctionType() as ftype:
                left_type = ftype.left
                left_kind = self._infer(left_type, env)
                if left_kind is not None:
                    assert left_kind == ATOM_KIND
                else:
                    self._assign(left_type, env, ATOM_KIND)

                right_type = ftype.right
                right_kind = self._infer(right_type, env)
                if right_kind is not None:
                    assert right_kind == ATOM_KIND
                else:
                    self._assign(right_type, env, ATOM_KIND)

                return ATOM_KIND

            case TypeScheme(vars, inner) as ts:
                child_env = env.child_env()
                ts.env = child_env
                for name in vars:
                    child_env.add(name, None)

                return self._infer(inner, child_env)

    def infer(self, type: Type, env: KindEnv):
        kind = self._infer(type, env)
        if kind is not None:
            assert kind == ATOM_KIND
        else:
            self._assign(type, env, ATOM_KIND)

        return ATOM_KIND


def kindof(type: Type, env: KindEnv) -> Kind:
    match type:
        case TypeConstant(name) | TypeVar(name):
            kind, found = env.get(name)
            assert found
            assert kind is not None

            return kind

        case TypeApp(f, args):
            f_kind = kindof(f, env)
            assert isinstance(f_kind, FunctionKind)

            match f_kind.args[len(args) :]:
                case [kind]:
                    return kind
                case kinds:
                    return FunctionKind(kinds)

        case FunctionType():
            return ATOM_KIND

        case TypeScheme(_, inner) as ts:
            return kindof(inner, ts.env)
