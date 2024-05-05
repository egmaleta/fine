from lark import Transformer, Lark

from . import ast
from .ast.utils import create_function, create_typed_function, typelist_of_ftype


class ASTBuilder(Transformer):
    def module(self, p):
        defn_list = []
        for defn in p[0]:
            if isinstance(defn, list):
                defn_list.extend(defn)
            else:
                defn_list.append(defn)

        return ast.Module(defn_list)

    def glob_defn_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def int_val_defn(self, p):
        name, id = p
        return ast.ValueDefn(name, ast.InternalValue(id))

    def int_fun_defn(self, p):
        name, params, id = p
        value = ast.InternalFunction(id, params)
        return ast.ValueDefn(name, create_function(params, value))

    def int_op_defn(self, p):
        left, name, right, id = p
        params = [left, right]
        value = ast.InternalFunction(id, params)
        return ast.ValueDefn(name, create_function(params, value))

    def int_adt_defn(self, p):
        return ast.ConcreteType(p[0])

    def adt_defn(self, p):
        if len(p) == 3:
            name, params, pairs = p
        else:
            name, pairs = p
            params = []

        if len(params) > 0:
            type = ast.PolyType(name, [ast.TypeVar(p) for p in params])
        else:
            type = ast.ConcreteType(name)

        defn_list = [type]
        for ct, t in pairs:
            if t is None:
                value = ast.NullaryData(ct, type)
            elif not isinstance(t, ast.FunctionType):
                param = "p1"
                data = ast.Data(ct, [param], type)

                value = ast.Function(param, data, t)
            else:
                param_types = typelist_of_ftype(t)
                params = [f"p{i+1}" for i in range(len(param_types))]
                data = ast.Data(ct, params, type)

                value = create_typed_function(params, param_types, data)

            defn_list.append(ast.Constructor(ct, value))

        return defn_list

    def adt_ct_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

    def adt_ct(self, p):
        if len(p) == 1:
            return (p[0], None)

        return (p[0], p[1])

    def fun_type_arg(self, p):
        if len(p) == 1:
            return p[0]

        left, right = p
        return ast.FunctionType(left, right)

    def var_type_arg(self, p):
        return ast.TypeVar(p[0])

    def null_type_arg(self, p):
        return ast.ConcreteType(p[0])

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
        return ast.ValueDefn(name, create_function(params, value))

    def op_defn(self, p):
        left, name, right, value = p
        return ast.ValueDefn(name, create_function([left, right], value))

    def typeof_defn(self, p):
        return ast.ValueTypeDefn(p[0], p[1])

    def fix_defn(self, p):
        fixity, prec, operators = p
        is_left_assoc = fixity.type == "INFIXL"
        prec = int(prec)

        if len(operators) == 1:
            return ast.FixitySignature(operators[0], is_left_assoc, prec)

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
        return ast.Function(p[0], p[1])

    def block_expr(self, p):
        return ast.Block(p[0], p[1])

    def let_expr(self, p):
        defn_list = []
        for defn in p[0]:
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
        return (p[0], p[1])

    def ct_pattern(self, p):
        if len(p) == 1:
            return ast.DataPattern(p[0])

        return ast.DataPattern(p[0], p[1])

    def single_pattern_list(self, p):
        if len(p) == 1:
            return p
        return [*p[0], p[1]]

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
        return ast.Id(p[0])

    def dec_literal(self, p):
        return ast.DecimalNumber(p[0])

    def nat_literal(self, p):
        return ast.IntegerNumber(p[0])

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
