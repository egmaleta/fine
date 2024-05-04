from abc import ABC
from lark.lexer import Token


type String = Token | str


class AST(ABC):
    pass


class Expr(AST):
    pass
