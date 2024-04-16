_ = None  # to suppress pylance warning
from .tools.lexer import Lexer


def _indent_len(s: str):
    try:
        i = s.rindex("\n")
        return len(s) - i - 1
    except ValueError:
        return 0


class Token:
    def __init__(self, lex: str, line: int, column: int):
        self.lex = lex
        self._start_pos = (column, line)
        self._end_pos = (column + len(lex), line)

    def start_pos(self):
        return self._start_pos

    def end_pos(self):
        return self._end_pos

    def __repr__(self):
        return repr(self.lex)

    def __str__(self):
        return self.lex


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
        "ID",
        "DEC",
        "NAT",
        "BTICK",
        "BSLASH",
        "SEMI",
        "UNIT",
        "EXT_OP",
        "ASSIGN",
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

    ID = r"[a-z_][a-zA-Z0-9_]*"

    DEC = r"(0|[1-9][0-9]*)\.[0-9]*"
    NAT = r"0|[1-9][0-9]*"

    BTICK = r"`"
    BSLASH = r"\\"
    SEMI = r";"

    UNIT = r"\(\)"

    EXT_OP = r"[~!@$%^&*/\-+|?.<>:=]{2,3}"

    ASSIGN = r"="

    OP = r"[~!@$%^&*/\-+|?.<>:]"

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
    def _token_in_token(tokens):
        end = 0
        for t in tokens:
            t.value = Token(t.value, t.lineno, t.index - end + 1)

            if t.type == "SPACE" and "\n" in t.value.lex:
                end = t.end - _indent_len(t.value.lex)

            yield t

    @staticmethod
    def _drop_spaces(tokens):
        for t in tokens:
            if t.type != "SPACE":
                yield t

    def tokenize(self, text, lineno=1, index=0):
        tokens = super().tokenize(text, lineno, index)
        tokens = self._token_in_token(tokens)
        return self._drop_spaces(tokens)
