from dataclasses import dataclass

from .base import AST, Expr
from .type import Type, INT_TYPE, FLOAT_TYPE, BOOL_TYPE, UNIT_TYPE
from ..utils import String


@dataclass
class InternalValue(Expr):
    """Value that cannot be represented in code.

    Therefore the evaluation of the value depends
    entirely on the compiler.

    `name` refers to identifier of the internal value."""

    name: String


@dataclass
class InternalFunction(InternalValue):
    """Function that cannot be represented in code.

    Therefore the evaluation of the function depends
    entirely on the compiler.

    `name` refers to identifier of the internal value."""

    params: list[String]


@dataclass
class NullaryData(Expr):
    value: String
    type: Type


class NaturalNumber(NullaryData):
    def __init__(self, value: String):
        super().__init__(value, INT_TYPE)


class DecimalNumber(NullaryData):
    def __init__(self, value: String):
        super().__init__(value, FLOAT_TYPE)


class Boolean(NullaryData):
    def __init__(self, value: String):
        super().__init__(value, BOOL_TYPE)


class Unit(NullaryData):
    def __init__(self, value: String):
        super().__init__(value, UNIT_TYPE)


@dataclass
class Data(Expr):
    name: String
    value_names: list[String]
    type: Type


@dataclass
class Id(Expr):
    value: String


@dataclass
class FunctionApp(Expr):
    target: Expr
    arg: Expr


@dataclass
class OpChain(Expr):
    elements: list[String | Expr]


@dataclass
class BinaryOperation(Expr):
    left: Expr
    operator: String
    right: Expr


@dataclass
class Function(Expr):
    param: String
    body: Expr
    param_type: Type | None = None


@dataclass
class LetExpr(Expr):
    definitions: list[AST]
    body: Expr


type SinglePattern = String | NullaryData
type Pattern = SinglePattern | DataPattern


@dataclass
class DataPattern(AST):
    name: String
    inner_patterns: list[SinglePattern] | None = None


@dataclass
class PatternMatching(Expr):
    matchable: Expr
    matches: list[tuple[Pattern, Expr]]


@dataclass
class Conditional(Expr):
    condition: Expr
    body: Expr
    fall_body: Expr


@dataclass
class ValueDefn(AST):
    name: String
    value: Expr


class Constructor(ValueDefn):
    pass


@dataclass
class ValueTypeDefn(AST):
    name: String
    type: Type


class ConstructorTypeDefn(ValueTypeDefn):
    pass


@dataclass
class FixitySignature(AST):
    operator: String
    is_left_associative: bool
    precedence: int


@dataclass
class Module(AST):
    definitions: list[AST]
