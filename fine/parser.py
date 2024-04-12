_ = None  # to suppress pylance warning
from .tools.parser import Parser
from .lexer import FineLexer, INDENT_TTYPE, DEDENT_TTYPE
from . import ast


class FineParser(Parser):
    tokens = FineLexer.tokens | {INDENT_TTYPE, DEDENT_TTYPE}

    start = "program"

    @_("")
    def empty(self, p):
        pass

    # program : decl_list
    #         | empty

    @_("decl_list")
    def program(self, p):
        pass

    @_("empty")
    def program(self, p):
        return None

    # decl_list : decl NEWLINE decl_list
    #           | decl

    @_("decl NEWLINE decl_list")
    def decl_list(self, p):
        return [p[0], *p[2]]

    @_("decl")
    def decl_list(self, p):
        return [p[0]]

    # decl : fixity NAT operator
    #      | name ASSIGN opt_ind_expr
    #      | ID id_list
    #      | name pattern_list ASSIGN opt_ind_expr

    @_("fixity NAT operator")
    def decl(self, p):
        fix = p[0]
        op = p[2]

        return ast.OperatorInfo(
            op.lex,
            fix.lex == "INFIXL",
            int(p[1].lex),
            start_pos=fix.pos,
            end_pos=(op.pos[0] + len(op.lex), op.pos[1]),
        )

    @_("name ASSIGN opt_ind_expr")
    def decl(self, p):
        return ast.ValueDecl(p[0].lex, p[2], start_pos=p[0].pos)

    @_("ID id_list")
    def decl(self, p):
        last = p[1][-1]

        return ast.FunctionParams(
            p[0].lex,
            [info.lex for info in p[1]],
            start_pos=p[0].pos,
            end_pos=(last.pos[0] + len(last.lex), last.pos[1]),
        )

    @_("name pattern_list ASSIGN opt_ind_expr")
    def decl(self, p):
        return ast.FunctionSegment(p[0].lex, p[1], p[3], start_pos=p[0].pos)

    # fixity : INFIXL
    #        | INFIXR

    @_("INFIXL", "INFIXR")
    def fixity(self, p):
        return p[0]

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

    # id_list : ID id_list
    #         | ID

    @_("ID id_list")
    def id_list(self, p):
        return [p[0], *p[1]]

    @_("ID")
    def id_list(self, p):
        return p[0]

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
        return ast.Identifier(p[0].lex, start_pos=p[0].pos)

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
        return (p[0].lex, p[2])

    # atom : OPAR expr CPAR
    #      | ID
    #      | literal

    @_("OPAR expr CPAR")
    def atom(self, p):
        return p[1]

    @_("ID")
    def atom(self, p):
        return ast.Identifier(p[0].lex, start_pos=p[0].pos)

    @_("literal")
    def atom(self, p):
        return p[0]

    # literal : NAT
    #         | DEC

    @_("NAT")
    def literal(self, p):
        return ast.NaturalNumber(p[0].lex, start_pos=p[0].pos)

    @_("DEC")
    def literal(self, p):
        return ast.DecimalNumber(p[0].lex, start_pos=p[0].pos)
