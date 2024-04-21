_ = None  # to suppress pylance warning
from vendor.sly.yacc import Parser as _Parser

from .lexer import Lexer
from . import ast


class Parser(_Parser):
    tokens = Lexer.TOKEN_TYPES
    debugfile = "parse.debug"
    start = "program"

    def parse(self, tokens) -> ast.Program | None:
        return super().parse(tokens)

    ## grammar

    @_("")
    def empty(self, p):
        pass

    # program

    @_("top_defn_list")
    def program(self, p):
        return ast.Program(p[0])

    @_("empty")
    def program(self, p):
        return None

    # top_defn_list

    @_("top_defn top_defn_list")
    def top_defn_list(self, p):
        return [p[0], *p[1]]

    @_("top_defn")
    def top_defn_list(self, p):
        return [p[0]]

    # top_defn

    @_("defn")
    def top_defn(self, p):
        return p[0]

    # defn_list

    @_("defn defn_list")
    def defn_list(self, p):
        return [p[0], *p[1]]

    @_("defn")
    def defn_list(self, p):
        return [p[0]]

    # defn

    @_("val_defn", "fun_defn", "op_info")
    def defn(self, p):
        return p[0]

    # val_defn

    @_("VAL name ASSIGN body_expr")
    def val_defn(self, p):
        return ast.ValueDefn(p[1], p[3])

    # fun_defn

    @_("FUN name params ASSIGN body_expr")
    def fun_defn(self, p):
        return ast.ValueDefn(
            p[1], ast.Function(p[2], p[4], lineno=p[0].lineno, index=p[0].index)
        )

    @_("FUN ID operator ID ASSIGN body_expr")
    def fun_defn(self, p):
        return ast.ValueDefn(
            p[2], ast.Function([p[1], p[3]], p[5], lineno=p[0].lineno, index=p[0].index)
        )

    # body_expr

    @_("expr")
    def body_expr(self, p):
        return p[0]

    @_("INTERNAL params")
    def body_expr(self, p):
        name, *params = p[1]
        return ast.InternalExpr(
            name.value, [p.value for p in params] if len(params) > 0 else None
        )

    # op_info

    @_("INFIXL NAT operator", "INFIXR NAT operator")
    def op_info(self, p):
        return ast.OperationInfo(p[2], p[0].type == "INFIXL", int(p[1].value))

    # params

    @_("ID params")
    def params(self, p):
        return [p[0], *p[1]]

    @_("ID")
    def params(self, p):
        return [p[0]]

    # name

    @_("ID")
    def name(self, p):
        return p[0]

    @_("OPAR EXT_OP CPAR", "OPAR OP CPAR")
    def name(self, p):
        return p[1]

    # operator

    @_("BTICK ID BTICK")
    def operator(self, p):
        return p[1]

    @_("EXT_OP", "OP")
    def operator(self, p):
        return p[0]

    # expr

    @_("BSLASH params ASSIGN expr")
    def expr(self, p):
        return ast.Function(p[1], p[3], lineno=p[0].lineno, index=p[0].index)

    @_("DO expr_list THEN expr")
    def expr(self, p):
        return ast.Block(p[1], p[3], lineno=p[0].lineno, index=p[0].index)

    @_("LET defn_list IN expr")
    def expr(self, p):
        return ast.LetExpr(p[1], p[3], lineno=p[0].lineno, index=p[0].index)

    @_("MATCH expr match_list")
    def expr(self, p):
        return ast.PatternMatching(p[1], p[2], lineno=p[0].lineno, index=p[0].index)

    @_("op_chain")
    def expr(self, p):
        chain = p[0]
        if len(chain) == 1:
            return chain[0]
        return ast.OpChain(chain)

    # expr_list

    @_("expr SEMI expr_list")
    def expr_list(self, p):
        return [p[0], *p[2]]

    @_("expr SEMI", "expr")
    def expr_list(self, p):
        return [p[0]]

    # match_list

    @_("match match_list")
    def match_list(self, p):
        return [p[0], *p[1]]

    @_("match")
    def match_list(self, p):
        return [p[0]]

    # match

    @_("BAR pattern ASSIGN expr")
    def match(self, p):
        return (p[1], p[3])

    # pattern

    @_("ID")
    def pattern(self, p):
        return ast.Identifier(p[0])

    @_("literal", "data_ct")
    def pattern(self, p):
        return p[0]

    # op_chain

    @_("operand operator op_chain")
    def op_chain(self, p):
        return [p[0], p[1], *p[2]]

    @_("operand")
    def op_chain(self, p):
        return [p[0]]

    # operand

    @_("atom args")
    def operand(self, p):
        fapp = p[0]
        for arg, name in p[1]:
            fapp = ast.FunctionApp(fapp, arg, name)
        return fapp

    # atom

    @_("OPAR expr CPAR")
    def atom(self, p):
        return p[1]

    @_("name")
    def atom(self, p):
        return ast.Identifier(p[0])

    @_("literal", "data_ct_id")
    def atom(self, p):
        return p[0]

    # literal

    @_("DEC")
    def literal(self, p):
        return ast.DecimalNumber(p[0])

    @_("NAT")
    def literal(self, p):
        return ast.NaturalNumber(p[0])

    @_("BOOL")
    def literal(self, p):
        return ast.Boolean(p[0])

    # data_ct

    @_("TYPE_ID", "UNIT")
    def data_ct(self, p):
        return ast.Data(p[0])

    # data_ct_id

    @_("TYPE_ID", "UNIT")
    def data_ct_id(self, p):
        return ast.Identifier(p[0])

    # args

    @_("ID ASSIGN atom args")
    def args(self, p):
        return [(p[2], p[0]), *p[3]]

    @_("atom args")
    def args(self, p):
        return [(p[0], None), *p[1]]

    @_("empty")
    def args(self, p):
        return []
