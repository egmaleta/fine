from typing import Optional

from .tools.ast import AST, Expr
from .lexer import Token


class Literal(Expr):
    def __init__(self, value: Token):
        self.value = value.lex

        self._start_pos = value.start_pos()
        self._end_pos = value.end_pos()

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self._end_pos


class NaturalNumber(Literal):
    pass


class DecimalNumber(Literal):
    pass


class Identifier(Literal):
    pass


class UnaryOp(Expr):
    def __init__(self, operator: Token, operand: Expr):
        self.operator = operator.lex
        self.operand = operand

        self._start_pos = operator.start_pos()

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self.operand.end_pos()


class BinOp(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator.lex
        self.right = right

    def start_pos(self):
        return self.left.start_pos()

    def end_pos(self):
        return self.right.end_pos()


class FunctionApp(Expr):
    def __init__(self, target: Expr, arg: Expr, arg_name: Optional[Token] = None):
        self.target = target
        self.arg = arg
        self.arg_name = arg_name.lex if arg_name else None

    def start_pos(self):
        return self.target.start_pos()

    def end_pos(self):
        return self.arg.end_pos()


class ValueDefn(AST):
    def __init__(self, name: Token, value: Expr):
        self.name = name.lex
        self.value = value


class OperatorInfo(AST):
    def __init__(self, assoc: Token, precedence: Token, operator: Token):
        self.operator = operator.lex
        self.is_left_assoc = assoc.lex == "INFIXL"
        self.precedence = int(precedence.lex)


class FunctionSegment(AST):
    def __init__(self, patterns: list[Expr], body: Expr):
        self.patterns = patterns
        self.body = body


class FunctionDefn(AST):
    def __init__(
        self,
        name: Token,
        param_names: Optional[list[Token]],
        segments: list[FunctionSegment],
    ):
        self.name = name.lex
        self.params = [t.lex for t in param_names] if param_names else None
        self.segments = segments


class Program(AST):
    def __init__(self, definitions: list[AST]):
        self.definitions = definitions
