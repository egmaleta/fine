from lark import Transformer, Lark

from . import ast


class ASTBuilder(Transformer):
    def module(self, p):
        defn_list = []
        for defn in p[0]:
            # fixity signatures
            if isinstance(defn, list):
                defn_list.extend(defn)
            else:
                defn_list.append(defn)

        return ast.Module(defn_list)

    def glob_defn_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def ext_val_defn(self, p):
        name, id = p
        return ast.ValueDefn(name, ast.ExternalExpr(id.value))

    def ext_fun_defn(self, p):
        name, params, id = p

        value = ast.ExternalFunction(id.value, [p.value for p in params])
        for p in params[::-1]:
            value = ast.Function(p, value)

        return ast.ValueDefn(name, value)

    def ext_op_defn(self, p):
        left, name, right, id = p
        params = [left, right]

        value = ast.ExternalFunction(id.value, [p.value for p in params])
        for p in params[::-1]:
            value = ast.Function(p, value)

        return ast.ValueDefn(name, value)

    def poly_type_defn(self, p):
        if len(p) == 3:
            type, args, cts = p
        else:
            type, args = p
            cts = []

        args = [ast.TypeVar(a) for a in args]
        return ast.TypeDefn(ast.PolyType(type, args), cts)

    def type_defn(self, p):
        if len(p) == 2:
            type, cts = p
        else:
            type = p[0]
            cts = []

        args = [ast.TypeVar(a) for a in args]
        return ast.TypeDefn(ast.Type(type), cts)

    def data_ct_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def data_ct(self, p):
        if len(p) == 1:
            return (p[0], None)

        return (p[0], p[1])

    def fun_type_arg(self, p):
        if len(p) == 1:
            return p[0]

        left, t, right = p
        return ast.PolyType(t, [left, right])

    def var_type_arg(self, p):
        return ast.TypeVar(p[0])

    def null_type_arg(self, p):
        return ast.Type(p[0])

    def poly_type_arg(self, p):
        return ast.PolyType(p[0], p[1])

    def type_arg_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def val_defn(self, p):
        name, value = p
        return ast.ValueDefn(name, value)

    def fun_defn(self, p):
        name, params, value = p

        for p in params[::-1]:
            value = ast.Function(p, value)

        return ast.ValueDefn(name, value)

    def op_defn(self, p):
        left, name, right, value = p
        params = [left, right]
        return ast.ValueDefn(name, ast.Function(params, value))

    def typeof_defn(self, p):
        return ast.TypeOfDefn(p[0], p[1])

    def fix_defn(self, p):
        fixity, prec, operators = p
        is_left_assoc = fixity.type == "INFIXL"
        prec = int(prec)

        return [ast.FixitySignature(op, is_left_assoc, prec) for op in operators]

    def operator_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def param_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def match_expr(self, p):
        return ast.PatternMatching(p[0], p[1])

    def func_expr(self, p):
        if len(p) == 2:
            return ast.Function(p[0], p[1])
        return ast.Function([], p[0])

    def block_expr(self, p):
        return ast.Block(p[0], p[1])

    def let_expr(self, p):
        defn_list = []
        for defn in p[0]:
            # fixity signatures
            if isinstance(defn, list):
                defn_list.extend(defn)
            else:
                defn_list.append(defn)

        expr = p[1]

        return ast.LetExpr(defn_list, expr)

    def cond_expr(self, p):
        return ast.Conditional(p[0], p[1], p[2])

    def op_chain_expr(self, p):
        chain = p[0]
        if len(chain) == 1:
            return chain[0]
        return ast.OpChain(chain)

    def action_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def defn_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def match_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def match(self, p):
        return (p[0], p[2])

    def id_pattern(self, p):
        return ast.Identifier(p[0])

    def ct_pattern(self, p):
        return ast.Data(p[0])

    def op_chain(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1], p[2]]

    def operand(self, p):
        if len(p) == 1:
            return p[0]
        return ast.FunctionApp(p[0], p[1])

    def expr_atom(self, p):
        return p[0]

    def id_atom(self, p):
        return ast.Identifier(p[0])

    def dec_literal(self, p):
        return ast.DecimalNumber(p[0])

    def nat_literal(self, p):
        return ast.NaturalNumber(p[0])

    def bool_literal(self, p):
        return ast.Boolean(p[0])

    def unit_literal(self, p):
        return ast.Unit(p[0])


PARSER = Lark.open(
    "fine.lark",
    start="module",
    parser="lalr",
    lexer="basic",
    transformer=ASTBuilder(),
)


def parse(text: str) -> ast.Module:
    return PARSER.parse(text)
