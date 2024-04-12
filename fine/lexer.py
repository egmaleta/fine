_ = None  # to suppress pylance warning
from .tools.lexer import Lexer


class LexemeInfo:
    def __init__(self, lex, line, column):
        self.lex = lex
        self.line = line
        self.column = column

    def __repr__(self):
        return repr(self.lex)

    def __str__(self):
        return self.lex


INDENT_TTYPE = "INDENT"
DEDENT_TTYPE = "DEDENT"


def indent_len(s: str):
    try:
        i = s.rindex("\n")
        return len(s) - i - 1
    except ValueError:
        return 0


class FineLexer(Lexer):
    tokens = {
        "INFIXL",
        "INFIXR",
        "ID",
        "DEC",
        "NAT",
        "EXT_OP",
        "ASSIGN",
        "OP",
        "OPAR",
        "CPAR",
        "NEWLINE",
    }

    # precedence over id
    INFIXL = r"infixl"
    INFIXR = r"infixr"

    ID = r"[a-z_][a-zA-Z0-9_]*"

    DEC = r"0|[1-9][0-9_]*\.[0-9_]*"
    NAT = r"0|[1-9][0-9_]*"

    EXT_OP = r"[~!@$%^&*/-+|?.<>:=]{2,3}"

    ASSIGN = r"="

    OP = r"[~!@$%^&*/-+|?.<>:]"

    OPAR = r"\("
    CPAR = r"\)"

    @_(r"\n\s*")
    def NEWLINE(self, t):
        self.lineno += t.value.count("\n")
        return t

    ignore_space = r"\s+"
    ignore_comment = r"#.*"

    def error(self, t):
        print(f"lexer error: bad char at line {self.lineno}: '{t.value[0]}'")
        self.index += 1

    @staticmethod
    def _merge_newline_tokens(tokens):
        nl_t = None
        for t in tokens:
            if t.type == "NEWLINE":
                if nl_t:
                    nl_t.value += t.value
                    nl_t.end = t.end
                else:
                    nl_t = t
            else:
                if nl_t:
                    yield nl_t
                    nl_t = None

                yield t

        # last newline token is dropped

    @staticmethod
    def _newline_to_indent_tokens(tokens):
        levels = [0]
        last_t = None

        for t in tokens:
            if t.type == "NEWLINE":
                current_level = levels[-1]
                level = indent_len(t.value)

                if level > current_level:
                    t.type = INDENT_TTYPE
                    levels.append(level)

                elif level < current_level:
                    t.type = DEDENT_TTYPE
                    levels.pop()

            yield t
            last_t = t

        if last_t:
            Token = type(last_t)
            while len(levels) > 1:
                t = Token()
                t.type = DEDENT_TTYPE
                t.value = ""
                t.lineno = last_t.lineno
                t.index = last_t.index
                t.end = last_t.end
                yield t

                levels.pop()

    @staticmethod
    def _create_lexeme_info(tokens):
        end = 0
        for t in tokens:
            t.value = LexemeInfo(t.value, t.lineno, t.index - end + 1)

            if "\n" in t.value.lex:
                end = t.end - indent_len(t.value.lex)

            yield t

    def tokenize(self, text, lineno=1, index=0):
        tokens = super().tokenize(text, lineno, index)
        tokens = self._merge_newline_tokens(tokens)
        tokens = self._newline_to_indent_tokens(tokens)
        return self._create_lexeme_info(tokens)
