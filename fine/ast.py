from abc import ABC
from typing import Protocol, runtime_checkable
from dataclasses import dataclass, field

from .tools.lexer import Token


@runtime_checkable
class Findable(Protocol):
    lineno: int
    index: int
    end: int


class AST(ABC):
    pass


class Expr(AST):
    pass


@dataclass
class Data(Expr):
    _value_token: Token
    value: str = field(init=False)

    def __post_init__(self):
        self.value = self._value_token.value

    @property
    def lineno(self):
        return self._value_token.lineno

    @property
    def index(self):
        return self._value_token.index

    @property
    def end(self):
        return self._value_token.end


class NaturalNumber(Data):
    pass


class DecimalNumber(Data):
    pass


@dataclass
class Identifier(Expr):
    _value_token: Token
    value: str = field(init=False)

    def __post_init__(self):
        self.value = self._value_token.value

    @property
    def lineno(self):
        return self._value_token.lineno

    @property
    def index(self):
        return self._value_token.index

    @property
    def end(self):
        return self._value_token.end


@dataclass
class FunctionApp(Expr):
    target: Expr
    arg: Expr
    _arg_name_token: Token | None
    arg_name: str | None = field(init=False)

    def __post_init__(self):
        t = self._arg_name_token
        self.arg_name = t.value if isinstance(t, Token) else None

    @property
    def lineno(self):
        return self.target.lineno

    @property
    def index(self):
        return self.target.index

    @property
    def end(self):
        return self.arg.end


@dataclass
class OpChain(Expr):
    """Sugar for a tree of BinOp"""

    elements: list[Expr | Token]


@dataclass
class BinOp(Expr):
    left: Expr
    _operator_token: Token
    operator: str = field(init=False)
    right: Expr

    def __post_init__(self):
        self.operator = self._operator_token.value

    @property
    def lineno(self):
        return self.left.lineno

    @property
    def index(self):
        return self.left.index

    @property
    def end(self):
        return self.right.end


@dataclass
class Function(Expr):
    _param_tokens: list[Token]
    params: list[str] = field(init=False)
    body: Expr
    lineno: int = field(kw_only=True)
    index: int = field(kw_only=True)

    def __post_init__(self):
        self.params = [t.value for t in self._param_tokens]

    @property
    def end(self):
        return self.body.end


@dataclass
class Block(Expr):
    actions: list[Expr]
    body: Expr
    lineno: int = field(kw_only=True)
    index: int = field(kw_only=True)

    @property
    def end(self):
        return self.body.end


@dataclass
class LetExpr(Expr):
    definitions: list[AST]
    body: Expr
    lineno: int = field(kw_only=True)
    index: int = field(kw_only=True)

    @property
    def end(self):
        return self.body.end


@dataclass
class PatternMatching(Expr):
    matchable: Expr
    matches: list[tuple[Identifier | Data, Expr]]
    lineno: int = field(kw_only=True)
    index: int = field(kw_only=True)

    @property
    def end(self):
        return self.matches[-1][1].end


@dataclass
class ValueDefn(AST):
    _name_token: Token
    name: str = field(init=False)
    value: Expr

    def __post_init__(self):
        self.name = self._name_token.value


@dataclass
class BinOpInfo(AST):
    _operator_token: Token
    operator: str = field(init=False)
    is_left_assoc: bool
    precedence: int

    def __post_init__(self):
        self.operator = self._operator_token.value


@dataclass
class Program(AST):
    definitions: list[AST]
