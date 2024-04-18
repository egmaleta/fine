_ = None  # to suppress pylance warning
from .tools.lexer import Lexer


class FineLexer(Lexer):
    TOKEN_TYPES = {
        "FUN",
        "VAL",
        "IF",
        "THEN",
        "ELSE",
        "DO",
        "INFIXL",
        "INFIXR",
        "LET",
        "IN",
        "MATCH",
        "DATA",
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
        "OPAR",
        "CPAR",
    }

    tokens = TOKEN_TYPES | {"SPACE"}

    # precedence over id
    FUN = r"fun"
    VAL = r"val"
    IF = r"if"
    THEN = r"then"
    ELSE = r"else"
    DO = r"do"
    INFIXL = r"infixl"
    INFIXR = r"infixr"
    LET = r"let"
    IN = r"in"
    MATCH = r"match"

    DATA = r"[A-Z][a-zA-Z0-9_]*|\(\)"
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

    OPAR = r"\("
    CPAR = r"\)"

    @_(r"\s+")
    def SPACE(self, t):
        self.lineno += t.value.count("\n")
        return t

    ignore_comment = r"#.*"

    def error(self, t):
        print(f"lexer error: bad char at line {self.lineno}: '{t.value[0]}'")
        self.index += 1

    @staticmethod
    def _drop_spaces(tokens):
        for t in tokens:
            if t.type != "SPACE":
                yield t

    def tokenize(self, text, lineno=1, index=0):
        tokens = super().tokenize(text, lineno, index)
        return self._drop_spaces(tokens)
