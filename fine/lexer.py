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
        return f"Token(type={repr(self.type)}, value={repr(self.value)}, column={self.column}, line={self.lineno})"


BEGIN_T = FineToken("BEGIN", "", -1, -1, -1, -1)
END_T = FineToken("END", "", -1, -1, -1, -1)


def indent_len(s: str):
    try:
        i = s.rindex("\n")
        return len(s) - i - 1
    except ValueError:
        return 0


class FineLexer(Lexer):
    TOKEN_TYPES = {
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
    def NL(self, t):
        self.lineno += t.value.count("\n")
        return t

    ignore_space = r"\s+"
    ignore_comment = r"#.*"

    def error(self, t):
        print(f"lexer error: bad char at line {self.lineno}: '{t.value[0]}'")
        self.index += 1

    @staticmethod
    def _merge_nl(tokens):
        end = 0
        nl_t = None
        for t in tokens:
            t = FineToken(t.type, t.value, t.lineno, t.index, t.end, t.index - end + 1)

            if t.type == "NL":
                end = t.end - indent_len(t.value)

                if nl_t:
                    nl_t = FineToken(
                        nl_t.type,
                        nl_t.value + t.value,
                        nl_t.lineno,
                        nl_t.index,
                        t.end,
                        nl_t.column,
                    )
                else:
                    nl_t = t
            else:
                if nl_t:
                    yield nl_t
                    nl_t = None

                yield t

    @staticmethod
    def _emit_indent(tokens):
        levels = [0]

        for t in tokens:
            if t.type != "NL":
                yield t
            else:
                current_level = levels[-1]
                level = indent_len(t.value)

                if level > current_level:
                    yield BEGIN_T
                    levels.append(level)

                elif level < current_level:
                    yield END_T
                    levels.pop()

        while len(levels) > 1:
            yield END_T
            levels.pop()

    def tokenize(self, text, lineno=1, index=0):
        return self._emit_indent(self._merge_nl(super().tokenize(text, lineno, index)))
