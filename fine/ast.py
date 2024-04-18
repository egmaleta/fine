from dataclasses import dataclass, field

from .tools.ast import AST, Expr


@dataclass
class Literal(Expr):
    value: str

    _lineno: int = field(kw_only=True)
    _index: int = field(kw_only=True)
    _end: int = field(kw_only=True)

    @property
    def lineno(self):
        return self._lineno

    @property
    def index(self):
        return self._index

    @property
    def end(self):
        return self._end


class NaturalNumber(Literal):
    pass


class DecimalNumber(Literal):
    pass


class Identifier(Literal):
    pass


@dataclass
class FunctionApp(Expr):
    target: Expr
    arg: Expr
    arg_name: str | None

    @property
    def lineno(self):
        return self.target.lineno

    @property
    def index(self):
        return self.target.index

    @property
    def index(self):
        return self.arg.end


@dataclass
class OpChain(Expr):
    elements: list[Expr | str]

    @property
    def lineno(self):
        return self.elements[0].lineno

    @property
    def index(self):
        return self.elements[0].index

    @property
    def end(self):
        return self.elements[-1].end


@dataclass
class BinOp(Expr):
    left: Expr
    operator: str
    right: Expr

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
    params: list[str]
    body: Expr

    _lineno: int = field(kw_only=True)
    _index: int = field(kw_only=True)

    @property
    def lineno(self):
        return self._lineno

    @property
    def index(self):
        return self._index

    @property
    def end(self):
        return self.body.end


@dataclass
class Conditional(Expr):
    condition: Expr
    body: Expr
    fall_body: Expr

    _lineno: int = field(kw_only=True)
    _index: int = field(kw_only=True)

    @property
    def lineno(self):
        return self._lineno

    @property
    def index(self):
        return self._index

    @property
    def end(self):
        return self.fall_body.end


@dataclass
class Block(Expr):
    actions: list[Expr]
    body: Expr

    _lineno: int = field(kw_only=True)
    _index: int = field(kw_only=True)

    @property
    def lineno(self):
        return self._lineno

    @property
    def index(self):
        return self._index

    @property
    def end(self):
        return self.body.end


@dataclass
class LetExpr(Expr):
    stmts: list[AST]
    body: Expr

    _lineno: int = field(kw_only=True)
    _index: int = field(kw_only=True)

    @property
    def lineno(self):
        return self._lineno

    @property
    def index(self):
        return self._index

    @property
    def end(self):
        return self.body.end


@dataclass
class PatternMatching(Expr):
    matchable: Expr
    matches: list[tuple[Literal, Expr]]

    _lineno: int = field(kw_only=True)
    _index: int = field(kw_only=True)

    @property
    def lineno(self):
        return self._lineno

    @property
    def index(self):
        return self._index

    @property
    def end(self):
        return self.matches[-1][1].end


@dataclass
class ValueDefn(AST):
    name: str
    value: Expr


@dataclass
class BinOpInfo(AST):
    operator: str
    is_left_assoc: bool
    precedence: int

    # .tools.scope._Named protocol impl
    def name(self):
        return self.operator


@dataclass
class Program(AST):
    stmts: list[AST]
