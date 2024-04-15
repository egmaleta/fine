_ = None  # to suppress pylance warning
from .tools.parser import Parser
from .lexer import FineLexer
from . import ast


class FineParser(Parser):
    tokens = FineLexer.tokens
    debugfile = "parse.debug"
    start = "program"

    def parse(self, tokens) -> ast.Program | None:
        return super().parse(tokens)

    ## grammar

    @_("")
    def empty(self, p):
        pass

    # program

    @_("stmt_list")
    def program(self, p):
        return ast.Program(p[0])

    @_("empty")
    def program(self, p):
        return None

    # stmt_list

    @_("stmt NEWLINE stmt_list", "stmt DEDENT stmt_list")
    def stmt_list(self, p):
        return [p[0], *p[2]]

    @_("stmt")
    def stmt_list(self, p):
        return [p[0]]

    # opt_ind_expr

    @_("INDENT expr")
    def opt_ind_expr(self, p):
        return p[1]

    @_("expr")
    def opt_ind_expr(self, p):
        return p[0]

    # stmt

    @_("val_defn", "fun_defn", "binop_info")
    def stmt(self, p):
        return p[0]

    # val_defn

    @_("name ASSIGN opt_ind_expr")
    def val_defn(self, p):
        return ast.ValueDefn(p[0], p[2])

    # fun_defn

    @_("name params ASSIGN opt_ind_expr")
    def fun_defn(self, p):
        return ast.FunctionDefn(p[0], p[1], p[3])

    @_("ID operator ID ASSIGN opt_ind_expr")
    def fun_defn(self, p):
        return ast.FunctionDefn(p[1], [p[0], p[2]], p[4])

    # binop_info

    @_("INFIXL NAT operator", "INFIXR NAT operator")
    def binop_info(self, p):
        return ast.BinOpInfo(p[0], p[1], p[2])

    # params

    @_("ID params")
    def params(self, p):
        return [p[0], *p[1]]

    @_("ID")
    def params(self, p):
        return [p[0]]

    # expr

    @_("op_chain")
    def expr(self, p):
        chain = p[0]
        if len(chain) == 1:
            return chain[0]
        return ast.OpChain(chain)

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

    @_("literal")
    def atom(self, p):
        return p[0]

    # name

    @_("ID")
    def name(self, p):
        return p[0]

    @_("OPAR EXT_OP CPAR", "OPAR OP CPAR")
    def name(self, p):
        return p[1]

    # literal

    @_("DEC")
    def literal(self, p):
        return ast.DecimalNumber(p[0])

    @_("NAT")
    def literal(self, p):
        return ast.NaturalNumber(p[0])

    @_("UNIT")
    def literal(self, p):
        return ast.Literal(p[0])

    # operator

    @_("EXT_OP", "OP")
    def operator(self, p):
        return p[0]

    @_("BTICK ID BTICK")
    def operator(self, p):
        return p[1]

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
