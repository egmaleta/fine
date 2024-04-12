from typing import Optional

from .tools.ast import AST, Expr


class Literal(Expr):
    def __init__(self, value: str, *, start_pos: tuple[int, int]):
        self.value = value

        self._start_pos = start_pos
        self._end_pos = (start_pos[0] + len(value), start_pos[1])

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
    def __init__(self, operator: str, operand: Expr, *, start_pos: tuple[int, int]):
        self.operator = operator
        self.operand = operand

        self._start_pos = start_pos

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self.operand.end_pos()


class BinOp(Expr):
    def __init__(self, left: Expr, operator: str, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    def start_pos(self):
        return self.left.start_pos()

    def end_pos(self):
        return self.right.end_pos()


class FunctionApp(Expr):
    def __init__(self, target: Expr, arg: Expr, arg_name: Optional[str] = None):
        self.target = target
        self.arg = arg
        self.arg_name = arg_name

    def start_pos(self):
        return self.target.start_pos()

    def end_pos(self):
        return self.arg.end_pos()


class ValueDecl(AST):
    def __init__(self, name: str, value: Expr, *, start_pos: tuple[int, int]):
        self.name = name
        self.value = value

        self._start_pos = start_pos

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self.value.end_pos()


class OperatorInfo(AST):
    def __init__(
        self,
        operator: str,
        left_assoc: bool,
        precedence: int,
        *,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
    ):
        self.operator = operator
        self.is_left_assoc = left_assoc
        self.precedence = precedence

        self._start_post = start_pos
        self._end_pos = end_pos

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self._end_pos


class FunctionSegment(AST):
    def __init__(
        self, name: str, patterns: list[Expr], body: Expr, *, start_pos: tuple[int, int]
    ):
        self.name = name
        self.patterns = patterns
        self.body = body

        self._start_pos = start_pos

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self.body.end_pos()


class FunctionParams(AST):
    def __init__(
        self,
        name: str,
        param_names: list[str],
        *,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
    ):
        self.name = name
        self.param_names = param_names

        self._start_pos = start_pos
        self._end_pos = end_pos

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self._end_pos
