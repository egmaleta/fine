_ = None  # to suppress pylance warning
from .tools.parser import Parser
from .lexer import FineLexer


class FineParser(Parser):
    tokens = FineLexer.tokens

    start = "program"

    @_("")
    def empty(self, p):
        pass

    # program

    @_("stmt_list")
    def program(self, p):
        pass

    @_("empty")
    def program(self, p):
        pass

    # stmt_list

    @_("stmt NEWLINE stmt_list")
    def stmt_list(self, p):
        pass

    @_("stmt DEDENT stmt_list")
    def stmt_list(self, p):
        pass

    @_("stmt")
    def stmt_list(self, p):
        pass

    # opt_ind_expr

    @_("INDENT expr")
    def opt_ind_expr(self, p):
        pass

    @_("expr")
    def opt_ind_expr(self, p):
        pass

    # stmt

    @_("val_defn")
    def stmt(self, p):
        pass

    @_("fun_defn")
    def stmt(self, p):
        pass

    @_("binop_info")
    def stmt(self, p):
        pass

    # val_defn

    @_("name ASSIGN opt_ind_expr")
    def val_defn(self, p):
        pass

    # fun_defn

    @_("name params ASSIGN opt_ind_expr")
    def fun_defn(self, p):
        pass

    @_("ID operator ID ASSIGN opt_ind_expr")
    def fun_defn(self, p):
        pass

    # binop_info

    @_("INFIXL NAT operator", "INFIXR NAT operator")
    def binop_info(self, p):
        pass

    # params

    @_("ID params")
    def params(self, p):
        pass

    @_("ID")
    def params(self, p):
        pass

    # expr

    @_("op_chain")
    def expr(self, p):
        pass

    # op_chain

    @_("operand operator op_chain")
    def op_chain(self, p):
        pass

    @_("operand")
    def op_chain(self, p):
        pass

    # operand

    @_("atom args")
    def operand(self, p):
        pass

    # atom

    @_("OPAR expr CPAR")
    def atom(self, p):
        pass

    @_("name", "literal")
    def atom(self, p):
        pass

    # name

    @_("ID")
    def name(self, p):
        pass

    @_("OPAR operator CPAR")
    def name(self, p):
        pass

    # literal

    @_("DEC")
    def literal(self, p):
        pass

    @_("NAT")
    def literal(self, p):
        pass

    # operator

    @_("EXT_OP", "OP")
    def operator(self, p):
        pass

    # args

    @_("ID ASSIGN atom args")
    def args(self, p):
        pass

    @_("atom")
    def args(self, p):
        pass

    @_("empty")
    def args(self, p):
        pass
