_ = None  # to suppress pylance warning
from typing import Generator
from vendor.sly.lex import Lexer as _Lexer, Token


class Lexer(_Lexer):
    TOKEN_TYPES = {
        "INTERNAL",
        "THEN",
        "DO",
        "INFIXL",
        "INFIXR",
        "LET",
        "IN",
        "MATCH",
        "BOOL",
        "TYPE_ID",
        "ID",
        "DEC",
        "NAT",
        "BTICK",
        "BSLASH",
        "SEMI",
        "EXT_OP",
        "ASSIGN",
        "BAR",
        "OP",
        "UNIT",
        "OPAR",
        "CPAR",
    }

    tokens = TOKEN_TYPES | {"SPACE"}

    INTERNAL = r"#internal"

    # precedence over id
    THEN = r"then"
    DO = r"do"
    INFIXL = r"infixl"
    INFIXR = r"infixr"
    LET = r"let"
    IN = r"in"
    MATCH = r"match"

    BOOL = r"true|false"

    TYPE_ID = r"[A-Z][a-zA-Z0-9_]*"
    ID = r"[a-z_][a-zA-Z0-9_]*"

    DEC = r"(0|[1-9][0-9]*)\.[0-9]*"
    NAT = r"0|[1-9][0-9]*"

    BTICK = r"`"
    BSLASH = r"\\"
    SEMI = r";"

    EXT_OP = r"[~!@$%^&*/\-+|?.<>:=]{2,3}"

    ASSIGN = r"="
    BAR = r"\|"

    OP = r"[~!@$%^&*/\-+?.<>:]"

    UNIT = r"\(\)"

    OPAR = r"\("
    CPAR = r"\)"

    @_(r"\s+")
    def SPACE(self, t: Token):
        self.lineno += t.value.count("\n")
        return t

    ignore_comment = r"#.*"

    def error(self, t: Token):
        print(f"lexer error: bad char at line {self.lineno}: '{t.value[0]}'")
        self.index += 1

    @staticmethod
    def _drop_spaces(tokens: Generator[Token, None, None]):
        for t in tokens:
            if t.type != "SPACE":
                yield t

    def tokenize(self, text: str, lineno=1, index=0):
        tokens = super().tokenize(text, lineno, index)
        return self._drop_spaces(tokens)
