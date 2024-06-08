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


@dataclass
class ConstraintKind(Kind):
    kind: Kind

    def __repr__(self):
        return (
            f"({self.kind})" if isinstance(self.kind, FunctionKind) else repr(self.kind)
        ) + " -> Constraint"


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
class ConstrainedType(Type):
    constraints: dict[String, set[String]]
    type: Type

    def __init__(self, constraints: list[tuple[String, list[String]]], type: Type):
        super().__init__()
        self.type = type

        self.constraints = {}
        for new_tclass_name, tvar_names in constraints:
            for name in tvar_names:
                tclass_names = self.constraints.get(name)
                if tclass_names is not None:
                    tclass_names.add(new_tclass_name)
                else:
                    self.constraints[name] = {new_tclass_name}

    def __len__(self):
        return len(self.type)


@dataclass
class TypeScheme(Type):
    vars: set[String]
    type: Type

    _env: KindEnv | None = field(init=False, compare=False, default=None)

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
                vars = {}
                for type in args:
                    vars |= self._quantify(type)
                return vars

            case ConstrainedType(_, inner):
                return self._quantify(inner)

            case TypeScheme(vars, inner):
                captured = self._quantify(inner)

                unused = vars - captured
                assert len(unused) == 0

                free = captured - vars
                return free

    def quantify(self, type: Type):
        free = self._quantify(type)

        if not isinstance(type, TypeScheme):
            return TypeScheme(free, type) if len(free) > 0 else type

        assert len(free) == 0

        return type


class KindInferer:
    def _assign(self, type: Type, env: KindEnv, kind: Kind):
        match type:
            case TypeVar(name) | TypeConstant(name):
                assert env.set(name, kind)

            case ConstrainedType(_, inner) | TypeScheme(_, inner):
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

            case ConstrainedType(constrs, inner):
                for tvar_name, tclass_names in constrs.items():
                    candidate = None
                    for name in tclass_names:
                        constr_kind, found = env.get(name)
                        assert found
                        assert isinstance(constr_kind, ConstraintKind)

                        if candidate is not None:
                            assert candidate == constr_kind.kind
                        else:
                            candidate = constr_kind.kind

                    assert env.set(tvar_name, candidate)

                return self._infer(inner, env)

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

        case ConstrainedType(_, inner):
            return kindof(inner, env)

        case TypeScheme(_, inner) as ts:
            return kindof(inner, ts.env)
