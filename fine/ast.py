from dataclasses import dataclass, field

from .pattern import Pattern
from .type import Type, TypeConstant, TypeVar, TypeApp
from .utils import String


type AST = Expr | Defn

type Expr = (
    InternalValue
    | InternalFunction
    | Data
    | PolyData
    | Int
    | Float
    | Str
    | Id
    | FunctionApp
    | OpChain
    | Guards
    | Function
    | PatternMatching
    | LetExpr
)

type Defn = Binding | Typing | DatatypeDefn | FixitySignature | Module


@dataclass
class InternalValue:
    """A value provided by the compiler.

    `name` is the identifier of the value."""

    name: String


@dataclass
class InternalFunction:
    """A function provided by the compiler.

    `name` is the identifier of the function.

    `arg_names` are the names of the values in scope expected to be passed to the function.
    """

    name: String
    arg_names: list[String]


@dataclass
class Data:
    """Data created by constant data constructors.

    `tag` is the name of the constructor and the actual data."""

    tag: String


@dataclass
class PolyData:
    """Data created by function data constructors.

    `tag` is the name of the constructor.

    `value_names` are the names of the values in scope used to create the piece of data.
    """

    tag: String
    value_names: list[String]


@dataclass
class Int:
    value: String


@dataclass
class Float:
    value: String


@dataclass
class Str:
    value: String


@dataclass
class Id:
    name: String


@dataclass
class FunctionApp:
    f: Expr
    arg: Expr


@dataclass
class OpChain:
    """Expected to be transformed in a tree of `FunctionApp`."""

    chain: list[String | Expr]


@dataclass
class Guards:
    conditionals: list[tuple[Expr, Expr]]
    fallback: Expr


@dataclass
class Function:
    params: list[tuple[String, bool]]
    body: Expr


@dataclass
class PatternMatching:
    matchable: Expr
    matches: list[tuple[Pattern, Expr]]


@dataclass
class LetExpr:
    defns: list["Binding"]
    body: Expr


@dataclass
class Binding:
    name: String
    value: Expr


@dataclass
class Typing:
    name: String
    type: Type


@dataclass
class DatatypeDefn:
    type: TypeConstant | TypeApp
    bindings: list[Binding] = field(default_factory=lambda: [])
    typings: list[Typing] = field(default_factory=lambda: [])

    def __post_init__(self):
        match self.type:
            case TypeApp(f, args):
                assert isinstance(f, TypeConstant)
                assert all(isinstance(targ, TypeVar) for targ in args)

        assert len(self.bindings) == len(self.typings)
        for binding, typing in zip(self.bindings, self.typings):
            assert binding.name == typing.name

    @property
    def is_internal(self):
        return len(self.typings) == 0


@dataclass
class FixitySignature:
    operators: list[String]
    is_left_associative: bool
    precedence: int


@dataclass
class Module:
    defns: list[Defn]
