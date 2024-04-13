_ = None  # to suppress pylance warning
from .tools.parser import Parser
from .lexer import FineLexer
from . import ast


class FineParser(Parser):
    tokens = FineLexer.tokens

    debugfile = "parser.out"

    start = "program"

    @_("")
    def empty(self, p):
        pass

    # program : defn_list
    #         | empty

    @_("defn_list")
    def program(self, p):
        return ast.Program(p[0])

    @_("empty")
    def program(self, p):
        return None

    # defn_list : defn NEWLINE defn_list
    #           | defn

    @_("defn NEWLINE defn_list")
    def defn_list(self, p):
        return [p[0], *p[2]]

    @_("defn")
    def defn_list(self, p):
        return [p[0]]

    # defn : INFIXL NAT operator
    #      | INFIXR NAT operator
    #      | VAL name ASSIGN opt_ind_expr
    #      | FUN name opt_param_list NEWLINE func_segments

    @_("INFIXL NAT operator", "INFIXR NAT operator")
    def defn(self, p):
        return ast.OperatorInfo(p[0], p[1], p[2])

    @_("VAL name ASSIGN opt_ind_expr")
    def defn(self, p):
        return ast.ValueDefn(p[1], p[3])

    @_("FUN name opt_param_list NEWLINE func_segments")
    def defn(self, p):
        return ast.FunctionDefn(p[1], p[2], p[4])

    # operator : OP
    #          | EXT_OP

    @_("OP", "EXT_OP")
    def operator(self, p):
        return p[0]

    # name : ID
    #      | OPAR operator CPAR

    @_("ID")
    def name(self, p):
        return p[0]

    @_("OPAR operator CPAR")
    def name(self, p):
        return p[1]

    # opt_ind_expr : INDENT expr DEDENT
    #              | expr

    @_("INDENT expr DEDENT")
    def opt_ind_expr(self, p):
        return p[1]

    @_("expr")
    def opt_ind_expr(self, p):
        return p[0]

    # opt_param_list : param_list
    #                | empty

    @_("param_list")
    def opt_param_list(self, p):
        return p[0]

    @_("empty")
    def opt_param_list(self, p):
        return None

    # param_list : ID param_list
    #            | ID

    @_("ID param_list")
    def param_list(self, p):
        return [p[0], *p[1]]

    @_("ID")
    def param_list(self, p):
        return [p[0]]

    # func_segments : func_seg NEWLINE func_segments
    #               | func_seg func_segments
    #               | func_seg

    @_("func_seg NEWLINE func_segments")
    def func_segments(self, p):
        return [p[0], *p[2]]

    @_("func_seg func_segments")
    def func_segments(self, p):
        return [p[0], *p[1]]

    @_("func_seg")
    def func_segments(self, p):
        return [p[0]]

    # func_seg : pattern_list ASSIGN opt_ind_expr

    @_("pattern_list ASSIGN opt_ind_expr")
    def func_seg(self, p):
        return ast.FunctionSegment(p[0], p[2])

    # pattern_list : pattern pattern_list
    #              | pattern

    @_("pattern pattern_list")
    def pattern_list(self, p):
        return [p[0], *p[1]]

    @_("pattern")
    def pattern_list(self, p):
        return [p[0]]

    # pattern : ID
    #         | literal

    @_("ID")
    def pattern(self, p):
        return ast.Identifier(p[0])

    @_("literal")
    def pattern(self, p):
        return p[0]

    # expr : op_chain

    @_("op_chain")
    def expr(self, p):
        # process chain of operations
        pass

    # op_chain : operand operator op_chain
    #          | operator op_chain
    #          | operand

    @_("operand operator op_chain")
    def op_chain(self, p):
        return [p[0], p[1], *p[2]]

    @_("operator op_chain")
    def op_chain(self, p):
        return [p[0], *p[1]]

    @_("operand")
    def op_chain(self, p):
        return [p[0]]

    # operand : atom arg_list
    #         | atom

    @_("atom arg_list")
    def operand(self, p):
        node = p[0]
        for arg in p[1]:
            if isinstance(arg, tuple):
                node = ast.FunctionApp(node, arg[1], arg[0])
            else:
                node = ast.FunctionApp(node, arg)

        return node

    @_("atom")
    def operand(self, p):
        return p[0]

    # arg_list : arg arg_list
    #          | arg

    @_("arg arg_list")
    def arg_list(self, p):
        return [p[0], *p[1]]

    @_("arg")
    def arg_list(self, p):
        return [p[0]]

    # arg : atom
    #     | ID ASSIGN atom

    @_("atom")
    def arg(self, p):
        return p[0]

    @_("ID ASSIGN atom")
    def arg(self, p):
        return (p[0], p[2])

    # atom : OPAR expr CPAR
    #      | ID
    #      | literal

    @_("OPAR expr CPAR")
    def atom(self, p):
        return p[1]

    @_("ID")
    def atom(self, p):
        return ast.Identifier(p[0])

    @_("literal")
    def atom(self, p):
        return p[0]

    # literal : NAT
    #         | DEC

    @_("NAT")
    def literal(self, p):
        return ast.NaturalNumber(p[0])

    @_("DEC")
    def literal(self, p):
        return ast.DecimalNumber(p[0])
