from dataclasses import dataclass, field

from .utils import String, Env


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


def check_kind(type: Type, env: KindEnv, expected_kind=ATOM_KIND):
    match type:
        case TypeConstant(name) | TypeVar(name):
            kind, found = env.get(name)
            assert found
            assert kind == expected_kind

        case TypeApp(f, args):
            fkind = kindof(f, env)

            for type_arg in args:
                assert isinstance(fkind, FunctionKind)
                check_kind(type_arg, env, fkind.left)
                fkind = fkind.right

            assert fkind == expected_kind

        case FunctionType() as ftype:
            check_kind(ftype.left, env, ATOM_KIND)
            check_kind(ftype.right, env, ATOM_KIND)

        case TypeScheme(_, inner):
            assert type._env is not None
            return check_kind(inner, type._env, expected_kind)


def kindof(type: Type, env: KindEnv) -> Kind:
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


type KindEnv = Env[Kind | None]


@dataclass
class _Equation:
    left: TypeConstant | TypeVar
    right: list[Type]
    env: KindEnv

    def __post_init__(self):
        _, found = self.env.get(self.left.name)
        assert found

    def solved(self):
        try:
            kind = kindof(self.left, self.env)
        except AssertionError:
            pass
        else:
            # solve right
            for t in self.right:
                if isinstance(t, (TypeConstant, TypeVar)):
                    tkind, found = self.env.get(t.name)
                    if found and tkind is None:
                        self.env.set(t.name, kind.left)
                kind = kind.right

            return True

        # solve left
        try:
            kind = FunctionKind([kindof(t, self.env) for t in self.right] + [ATOM_KIND])
        except AssertionError:
            pass
        else:
            self.env.set(self.left.name, kind)
            return True

        return False


class KindInferer:
    def __init__(self):
        self._equations: list[_Equation] = []
        self._tvar_names: list[String] = []

    def _assign(self, type: Type, kind: Kind, env: KindEnv):
        assert isinstance(type, (TypeConstant, TypeVar))
        assert env.set(type.name, kind)

    def _infer(self, type: Type, env: KindEnv):
        match type:
            case TypeConstant(name):
                kind, found = env.get(name)
                assert found
                return kind

            case TypeVar(name):
                self._tvar_names.append(name)

                kind, found = env.get(name)
                assert found
                return kind

            case TypeApp(f, args):
                fkind = self._infer(f, env)

                if fkind is None:
                    kinds = [self._infer(type_arg, env) for type_arg in args]
                    if None not in kinds:
                        self._assign(f, FunctionKind([*kinds, ATOM_KIND]), env)
                    else:
                        eq = _Equation(f, args, env)
                        self._equations.append(eq)
                else:
                    for type_arg in args:
                        assert isinstance(fkind, FunctionKind)
                        lkind = fkind.left

                        kind = self._infer(type_arg, env)
                        if kind is None:
                            self._assign(type_arg, lkind, env)

                        fkind = fkind.right

                return ATOM_KIND

            case FunctionType() as ftype:
                # kind(->) == * -> *
                for type_arg in [ftype.left, ftype.right]:
                    kind = self._infer(type_arg, env)
                    if kind is None:
                        self._assign(type_arg, ATOM_KIND, env)

                return ATOM_KIND

            case TypeScheme(vars, inner):
                env = env.child_env()
                for name in vars:
                    env.add(name, None)

                if type._env is None:
                    type._env = env

                kind = self._infer(inner, env)
                if kind is None:
                    self._assign(inner, ATOM_KIND, env)

                return ATOM_KIND

    def infer(self, types: list[Type], env: KindEnv):
        for type in types:
            kind = self._infer(type, env)
            if kind is None:
                self._assign(type, ATOM_KIND, env)

        leftside_names = [eq.left.name for eq in self._equations]
        while True:
            prev_len = len(self._equations)

            self._equations = [eq for eq in self._equations if not eq.solved()]
            new_len = len(self._equations)

            if new_len == 0:
                return

            if new_len < prev_len:
                continue

            for name in self._tvar_names:
                if name not in leftside_names:
                    for eq in self._equations:
                        kind, found = eq.env.get(name)
                        if found and kind is None:
                            eq.env.set(name, ATOM_KIND)
                    self._tvar_names.remove(name)
                    break
            else:
                assert False, self._equations

    def silly_infer(self, type: Type, env: KindEnv):
        match type:
            case TypeConstant(name):
                env.set(name, ATOM_KIND)
            case TypeApp(f, args):
                assert isinstance(f, TypeConstant)
                assert all(isinstance(type_arg, TypeVar) for type_arg in args)

                env.set(f.name, FunctionKind([ATOM_KIND for _ in args] + [ATOM_KIND]))
            case _:
                assert False
