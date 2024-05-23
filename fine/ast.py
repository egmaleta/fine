from dataclasses import dataclass, field

from .pattern import Pattern
from .type import Type, TypeConstant, TypeApp
from .utils import String


class AST:
    pass


class Defn(AST):
    pass


class Expr(AST):
    pass


@dataclass
class InternalValue(Expr):
    """A value provided by the compiler.

    `name` is the identifier of the value."""

    name: String


@dataclass
class InternalFunction(Expr):
    """A function provided by the compiler.

    `name` is the identifier of the function.

    `arg_names` are the names of the values in scope expected to be passed to the function.
    """

    name: String
    arg_names: list[String]


@dataclass
class Data(Expr):
    """Data created by constant data constructors.

    `tag` is the name of the constructor and the actual data."""

    tag: String


@dataclass
class PolyData(Expr):
    """Data created by function data constructors.

    `tag` is the name of the constructor.

    `value_names` are the names of the values in scope used to create the piece of data.
    """

    tag: String
    value_names: list[String]


@dataclass
class NaturalNumber(Expr):
    value: String


@dataclass
class DecimalNumber(Expr):
    value: String


@dataclass
class Boolean(Expr):
    value: String


@dataclass
class Unit(Expr):
    value: String


@dataclass
class Id(Expr):
    name: String


@dataclass
class FunctionApp(Expr):
    f: Expr
    arg: Expr


@dataclass
class OpChain(Expr):
    """Expected to be transformed in a tree of `BinaryOperation`."""

    chain: list[String | Expr]


@dataclass
class BinaryOperation(Expr):
    left: Expr
    operator: String
    right: Expr


@dataclass
class LetExpr(Expr):
    definitions: list[Defn]
    body: Expr


@dataclass
class PatternMatching(Expr):
    matchable: Expr
    matches: list[tuple[Pattern, Expr]]


@dataclass
class MultiFunction(Expr):
    """Expected to be transformed in a nested `Function`."""

    params: list[String]
    body: Expr


@dataclass
class Function(Expr):
    param: String
    body: Expr


@dataclass
class ValueDefn(Defn):
    name: String
    value: Expr


@dataclass
class ValueTypeDefn(Defn):
    name: String
    type: Type


@dataclass
class DatatypeDefn(Defn):
    type: TypeConstant | TypeApp
    constructors: list[tuple[ValueDefn, Type]] = field(default_factory=lambda: [])

    typename: str = field(init=False)

    def __post_init__(self):
        t = self.type
        if isinstance(t, TypeApp):
            assert isinstance(t.f, TypeConstant)
            self.typename = t.f.name
        else:
            self.typename = t.name


@dataclass
class FixitySignature(Defn):
    operator: String
    is_left_associative: bool
    precedence: int


@dataclass
class Module(Defn):
    definitions: list[Defn]
