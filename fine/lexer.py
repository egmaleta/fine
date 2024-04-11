from .tools.lexer import Lexer


class FineToken:
    def __init__(self, type, value, lineno, index, end, column):
        super().__init__()
        self.type = type
        self.value = value
        self.lineno = lineno
        self.index = index
        self.end = end
        self.column = column

    @property
    def pos(self):
        return self.column, self.lineno

    def __repr__(self):
        return f"Token(type='{self.type}', value='{self.value}', column={self.column}, line={self.lineno})"


class FineLexer(Lexer):
    TOKEN_TYPES = {
        "FUN",
        "VAL",
        "INFIXL",
        "INFIXR",
        "ID",
        "DEC",
        "NAT",
        "CUSTOM_OP",
        "ASSIGN",
        "SINGLE_OP",
        "OPAR",
        "CPAR",
    }

    tokens = TOKEN_TYPES | {"NL"}

    # precedence over id
    FUN = r"fun"
    VAL = r"val"
    INFIXL = r"infixl"
    INFIXR = r"infixr"

    ID = r"[a-z_]\w*"

    DEC = r"0|[1-9][0-9_]*\.[0-9_]*"
    NAT = r"0|[1-9][0-9_]*"

    CUSTOM_OP = r"[~!@$%^&*-+|?.<>:=]{2,3}"

    ASSIGN = r"="

    SINGLE_OP = r"[~!@$%^&*-+|?.<>:]"

    OPAR = r"\("
    CPAR = r"\)"

    @_(r"\n+")
    def NL(self, t):
        self.lineno += len(t.value)
        return t

    ignore = " \t"
    ignore_comment = r"#.*"

    def error(self, t):
        print(f"lexer error: bad char at line {self.lineno}: '{t.value[0]}'")
        self.index += 1

    def tokenize(self, text, lineno=1, index=0):
        end = 0
        for t in super().tokenize(text, lineno, index):
            if t.type == "NL":
                end = t.end
            else:
                yield FineToken(
                    t.type, t.value, t.lineno, t.index, t.end, t.index - end + 1
                )
