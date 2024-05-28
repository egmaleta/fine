from dataclasses import dataclass, field
from lark.lexer import Token

from .pattern import Pattern
from .type import Type, TypeConstant, TypeApp


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

    name: Token


@dataclass
class InternalFunction(Expr):
    """A function provided by the compiler.

    `name` is the identifier of the function.

    `arg_names` are the names of the values in scope expected to be passed to the function.
    """

    name: Token
    arg_names: list[Token]


@dataclass
class Data(Expr):
    """Data created by constant data constructors.

    `tag` is the name of the constructor and the actual data."""

    tag: Token


@dataclass
class PolyData(Expr):
    """Data created by function data constructors.

    `tag` is the name of the constructor.

    `value_names` are the names of the values in scope used to create the piece of data.
    """

    tag: Token
    value_names: list[Token]


@dataclass
class NaturalNumber(Expr):
    value: Token


@dataclass
class DecimalNumber(Expr):
    value: Token


@dataclass
class Unit(Expr):
    value: Token


@dataclass
class Id(Expr):
    name: Token


@dataclass
class FunctionApp(Expr):
    f: Expr
    arg: Expr


@dataclass
class OpChain(Expr):
    """Expected to be transformed in a tree of `BinaryOperation`."""

    chain: list[Token | Expr]


@dataclass
class BinaryOperation(Expr):
    left: Expr
    operator: Token
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
class Function(Expr):
    params: list[Token]
    body: Expr


@dataclass
class ValueDefn(Defn):
    name: Token
    value: Expr


@dataclass
class ValueTypeDefn(Defn):
    name: Token
    type: Type


@dataclass
class DatatypeDefn(Defn):
    type: TypeConstant | TypeApp
    constructors: list[tuple[ValueDefn, Type]] = field(default_factory=lambda: [])

    typename: str = field(init=False)

    def __post_init__(self):
        t = self.type
        if isinstance(t, TypeApp):
            self.typename = t.fname
        else:
            self.typename = t.name


@dataclass
class FixitySignature(Defn):
    operators: list[Token]
    is_left_associative: bool
    precedence: int


@dataclass
class Module(Defn):
    definitions: list[Defn]
