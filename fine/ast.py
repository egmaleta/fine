from abc import ABC
from dataclasses import dataclass, field
from lark.lexer import Token


class AST(ABC):
    pass


class Expr(AST):
    pass


@dataclass
class Type(AST):
    _name_token: Token = field(repr=False)
    name: str = field(init=False)

    def __post_init__(self):
        self.name = self._name_token.value


class TypeVar(Type):
    pass


@dataclass
class PolyType(Type):
    args: list[Type]


@dataclass
class ExternalExpr(Expr):
    """Expression that cannot be represented in code.

    Therefore the evaluation of the expression depends
    entirely on the compiler."""

    id: str


@dataclass
class ExternalFunction(ExternalExpr):
    params: list[str]


@dataclass
class Data(Expr):
    _value_token: Token = field(repr=False)
    value: str = field(init=False)

    def __post_init__(self):
        self.value = self._value_token.value


class NaturalNumber(Data):
    pass


class DecimalNumber(Data):
    pass


class Boolean(Data):
    pass


class Unit(Data):
    pass


@dataclass
class Identifier(Expr):
    _value_token: Token = field(repr=False)
    value: str = field(init=False)

    def __post_init__(self):
        self.value = self._value_token.value


@dataclass
class FunctionApp(Expr):
    target: Expr
    arg: Expr


@dataclass
class OpChain(Expr):
    """Sugar for a tree of Operation"""

    elements: list[Token | Expr]


@dataclass
class Operation(Expr):
    left: Expr
    _operator_token: Token = field(repr=False)
    operator: str = field(init=False)
    right: Expr

    def __post_init__(self):
        self.operator = self._operator_token.value


@dataclass
class Function(Expr):
    _param_token: Token = field(repr=False)
    param: str = field(init=False)
    param_type: Type | None = field(init=False, default=None)
    body: Expr

    def __post_init__(self):
        self.param = self._param_token.value


@dataclass
class Block(Expr):
    actions: list[Expr]
    body: Expr


@dataclass
class LetExpr(Expr):
    definitions: list[AST]
    body: Expr


@dataclass
class PatternMatching(Expr):
    matchable: Expr
    matches: list[tuple[Identifier | Data, Expr]]


@dataclass
class Conditional(Expr):
    condition: Expr
    body: Expr
    fall_body: Expr


@dataclass
class ValueDefn(AST):
    _name_token: Token = field(repr=False)
    name: str = field(init=False)
    value: Expr
    is_constructor: bool = False

    def __post_init__(self):
        self.name = self._name_token.value


@dataclass
class FixitySignature(AST):
    _operator_token: Token = field(repr=False)
    operator: str = field(init=False)
    is_left_associative: bool
    precedence: int

    def __post_init__(self):
        self.operator = self._operator_token.value


@dataclass
class TypeOfDefn(AST):
    _name_token: Token = field(repr=False)
    name: str = field(init=False)
    type: Type

    def __post_init__(self):
        self.name = self._name_token.value


@dataclass
class TypeDefn(AST):
    type: Type
    constructors: list[tuple[Token, Type | None]]


@dataclass
class Module(AST):
    definitions: list[AST]
