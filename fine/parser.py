from lark import Transformer, Lark

from . import ast
from . import pattern as pat
from . import type as t


class ASTBuilder(Transformer):
    def module(self, p):
        return ast.Module(p)

    def int_val_defn(self, p):
        name, id = p
        return ast.ValueDefn(name, ast.InternalValue(id))

    def int_fun_defn(self, p):
        name, params, id = p
        value = ast.InternalFunction(id, params)
        return ast.ValueDefn(name, ast.Function(params, value))

    def int_op_defn(self, p):
        left, name, right, id = p
        params = [left, right]
        value = ast.InternalFunction(id, params)
        return ast.ValueDefn(name, ast.Function(params, value))

    def int_adt_defn(self, p):
        match p:
            case [name]:
                return ast.DatatypeDefn(t.TypeConstant(name))
            case [name, params]:
                return ast.DatatypeDefn(
                    t.TypeApp(t.TypeConstant(name), [t.TypeVar(p) for p in params])
                )

    @staticmethod
    def _create_datatype_defn(ct_type, cts):
        constructors = []

        for ct, type in cts:
            match type:
                case None:
                    value_defn = ast.ValueDefn(ct, ast.Data(ct))
                    constructors.append((value_defn, ct_type))

                case t.FunctionType(inner_types):
                    params = [f"param_{i+1}" for i in range(len(inner_types))]
                    value = ast.Function(params, ast.PolyData(ct, params))
                    value_defn = ast.ValueDefn(ct, value)

                    constructors.append(
                        (value_defn, t.FunctionType([*inner_types, ct_type]))
                    )

                case _:
                    params = ["param_1"]
                    value = ast.Function(params, ast.PolyData(ct, params))
                    value_defn = ast.ValueDefn(ct, value)

                    constructors.append((value_defn, t.FunctionType([type, ct_type])))

        return ast.DatatypeDefn(ct_type, constructors)

    def adt_defn(self, p):
        match p:
            case [name, cts]:
                type = t.TypeConstant(name)
                return self._create_datatype_defn(type, cts)

            case [name, params, cts]:
                type = t.TypeApp(name, [t.TypeVar(p) for p in params])
                return self._create_datatype_defn(type, cts)

    def adt_ct_list(self, p):
        return p

    def adt_ct(self, p):
        match p:
            case [ct]:
                return (ct, None)

            case [ct, type]:
                return (ct, type)

    def quantified_type(self, p):
        match p:
            case [ftype]:
                return ftype

            case [params, _, ftype]:
                return t.QuantifiedType(params, ftype)

    def fun_type(self, p):
        match p:
            case [type]:
                return type

            case _:
                return t.FunctionType(p)

    def type_var(self, p):
        return t.TypeVar(p[0])

    def mono_type(self, p):
        return t.TypeConstant(p[0])

    def poly_type(self, p):
        fname, *args = p
        return t.TypeApp(fname, args)

    def val_defn(self, p):
        name, value = p
        return ast.ValueDefn(name, value)

    def fun_defn(self, p):
        name, params, value = p
        return ast.ValueDefn(name, ast.Function(params, value))

    def op_defn(self, p):
        left, name, right, value = p
        return ast.ValueDefn(name, ast.Function([left, right], value))

    def typeof_defn(self, p):
        return ast.ValueTypeDefn(p[0], p[1])

    def fix_defn(self, p):
        fixity, prec, *operators = p

        return ast.FixitySignature(operators, fixity.type == "INFIXL", int(prec))

    def param_list(self, p):
        return p

    def match_expr(self, p):
        matchable, *matches = p
        return ast.PatternMatching(matchable, matches)

    def func_expr(self, p):
        return ast.Function(p[0], p[1])

    def let_expr(self, p):
        *defns, body = p
        return ast.LetExpr(defns, body)

    def cond_expr(self, p):
        return ast.Conditional(p[0], p[1], p[2])

    def op_chain_expr(self, p):
        match p:
            case [operand]:
                return operand

            case [left, op, right]:
                return ast.BinaryOperation(left, op, right)

            case _:
                return ast.OpChain(p)

    def match(self, p):
        return (p[0], p[1])

    def capture_pattern(self, p):
        return pat.CapturePattern(p[0])

    def data_pattern(self, p):
        tag, *patterns = p
        return pat.DataPattern(tag, patterns)

    def literal_pattern(self, p):
        return pat.LiteralPattern(p[0])

    def operand(self, p):
        match p:
            case [f, arg]:
                return ast.FunctionApp(f, arg)

            case [atom]:
                return atom

    def expr_atom(self, p):
        return p[0]

    def id_atom(self, p):
        return ast.Id(p[0])

    def dec_literal(self, p):
        return ast.DecimalNumber(p[0])

    def nat_literal(self, p):
        return ast.NaturalNumber(p[0])

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
