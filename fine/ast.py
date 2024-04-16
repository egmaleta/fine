from .tools.ast import AST, Expr
from .lexer import Token, FineLexer


class Program(AST):
    def __init__(self, definitions: list[AST]):
        self.definitions = definitions


class ValueDefn(AST):
    def __init__(self, name: Token, value: Expr):
        self.name = name.lex
        self.value = value


class BinOpInfo(AST):
    def __init__(self, assoc: Token, precedence: Token, operator: Token):
        self.operator = operator.lex
        self.is_left_assoc = assoc.lex == FineLexer.INFIXL
        self.precedence = int(precedence.lex)

    # .tools.scope._Named protocol impl
    def name(self):
        return self.operator


class OpChain(Expr):
    def __init__(self, elements: list[Expr | Token]):
        self.elements = elements

    def start_pos(self):
        return self.elements[0].start_pos()

    def end_pos(self):
        return self.elements[-1].end_pos()


class BinOp(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator.lex
        self.right = right

    def start_pos(self):
        return self.left.start_pos()

    def end_pos(self):
        return self.right.end_pos()


class Function(Expr):
    def __init__(self, params: list[Token], body: Expr, *, start_pos: tuple[int, int]):
        self.params = [t.lex for t in params]
        self.body = body

        self._start_pos = start_pos

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self.body.end_pos()


class Conditional(Expr):
    def __init__(
        self,
        condition: Expr,
        body: Expr,
        fall_body: Expr,
        *,
        start_pos: tuple[int, int],
    ):
        self.condition = condition
        self.body = body
        self.fall_body = fall_body

        self._start_pos = start_pos

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self.fall_body.end_pos()


class Block(Expr):
    def __init__(self, actions: list[Expr], body: Expr, *, start_pos: tuple[int, int]):
        self.actions = actions
        self.body = body

        self._start_pos = start_pos

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self.body.end_pos()


class FunctionApp(Expr):
    def __init__(self, target: Expr, arg: Expr, arg_name: Token | None):
        self.target = target
        self.arg = arg
        self.arg_name = arg_name.lex if arg_name else None

    def start_pos(self):
        return self.target.start_pos()

    def end_pos(self):
        return self.arg.end_pos()


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
