from dataclasses import dataclass

from .utils import String


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
        for new_tclass, tvars in constraints:
            for tvar in tvars:
                tclasses = self.constraints.get(tvar)
                if tclasses is not None:
                    tclasses.add(new_tclass)
                else:
                    self.constraints[tvar] = {new_tclass}

    def __len__(self):
        return len(self.type)


@dataclass
class TypeScheme(Type):
    vars: set[String]
    type: Type

    def __post_init__(self):
        if isinstance(self.vars, list):
            self.vars = set(self.vars)

    def __len__(self):
        return len(self.type)


def _quantify(type: Type):
    match type:
        case TypeConstant():
            return set()

        case TypeVar(name):
            return {name}

        case TypeApp(f, args):
            vars = _quantify(f)
            for type in args:
                vars |= _quantify(type)
            return vars

        case FunctionType(args):
            vars = {}
            for type in args:
                vars |= _quantify(type)
            return vars

        case ConstrainedType(_, inner):
            return _quantify(inner)

        case TypeScheme(vars, inner):
            captured = _quantify(inner)

            unused = vars - captured
            assert len(unused) == 0

            free = captured - vars
            return free


def quantify(type: Type):
    free = _quantify(type)

    if not isinstance(type, TypeScheme):
        return TypeScheme(free, type) if len(free) > 0 else type

    assert len(free) == 0

    return type
