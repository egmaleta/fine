from .tools.lexer import Lexer


def suffix_len(s: str, suffix_start: str):
    try:
        i = s.rindex(suffix_start)
        return len(s) - i - 1
    except ValueError:
        return 0


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
        return f"Token(type={repr(self.type)}, value={repr(self.value)}, column={self.column}, line={self.lineno})"


class FineLexer(Lexer):
    tokens = {
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
        "INDENT",
    }

    # precedence over id
    FUN = r"fun"
    VAL = r"val"
    INFIXL = r"infixl"
    INFIXR = r"infixr"

    ID = r"[a-z_][a-zA-Z0-9_]*"

    DEC = r"0|[1-9][0-9_]*\.[0-9_]*"
    NAT = r"0|[1-9][0-9_]*"

    CUSTOM_OP = r"[~!@$%^&*-+|?.<>:=]{2,3}"

    ASSIGN = r"="

    SINGLE_OP = r"[~!@$%^&*-+|?.<>:]"

    OPAR = r"\("
    CPAR = r"\)"

    @_(r"\n\s*")
    def INDENT(self, t):
        self.lineno += t.value.count("\n")
        return t

    ignore_space = r"\s+"
    ignore_comment = r"#.*"

    def error(self, t):
        print(f"lexer error: bad char at line {self.lineno}: '{t.value[0]}'")
        self.index += 1

    def tokenize(self, text, lineno=1, index=0):
        end = 0
        indent_t = None

        for t in super().tokenize(text, lineno, index):
            t = FineToken(t.type, t.value, t.lineno, t.index, t.end, t.index - end + 1)

            if t.type == "INDENT":
                end = t.end - suffix_len(t.value, "\n")

                if indent_t:
                    indent_t = FineToken(
                        indent_t.type,
                        indent_t.value + t.value,
                        indent_t.lineno,
                        indent_t.index,
                        t.end,
                        indent_t.column,
                    )
                else:
                    indent_t = t
            else:
                if indent_t:
                    yield indent_t
                    indent_t = None

                yield t
