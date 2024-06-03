from lark import Transformer, Lark

from . import ast
from . import pattern as pat
from . import type as t


class ASTBuilder(Transformer):
    def module(self, p):
        return ast.Module(p)

    def int_data_defn(self, p):
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

        for ct_name, type in cts:
            match type:
                case None:
                    value_defn = ast.ValueDefn(ct_name, ast.Data(ct_name))
                    constructors.append((value_defn, ct_type))

                case _:
                    ftype = (
                        t.FunctionType([*type.args, ct_type])
                        if isinstance(type, t.FunctionType)
                        else t.FunctionType([type, ct_type])
                    )
                    params = [f"_{i+1}" for i in range(len(ftype) - 1)]
                    value_defn = ast.ValueDefn(
                        ct_name, ast.Function(params, ast.PolyData(ct_name, params))
                    )
                    constructors.append((value_defn, ftype))

        return ast.DatatypeDefn(ct_type, constructors)

    def data_defn(self, p):
        match p:
            case [name, cts]:
                type = t.TypeConstant(name)
                return self._create_datatype_defn(type, cts)

            case [name, params, cts]:
                type = t.TypeApp(t.TypeConstant(name), [t.TypeVar(p) for p in params])
                return self._create_datatype_defn(type, cts)

    def int_val_defn(self, p):
        match p:
            case [name, intr]:
                return ast.ValueDefn(name, ast.InternalValue(intr))
            case [name, params, intr]:
                return ast.ValueDefn(
                    name, ast.Function(params, ast.InternalFunction(intr, params))
                )

    def int_op_defn(self, p):
        left, op, right, intr = p
        params = [left, right]
        return ast.ValueDefn(
            op, ast.Function(params, ast.InternalFunction(intr, params))
        )

    def datact_list(self, p):
        return p

    def datact(self, p):
        match p:
            case [ct]:
                return (ct, None)
            case [ct, type]:
                return (ct, type)

    def full_type(self, p):
        match p:
            case [ftype]:
                return ftype
            case [constrs, ftype]:
                return t.ConstrainedType(constrs, ftype)
            case [vars, _, ftype]:
                return t.TypeScheme(vars, ftype)
            case [vars, _, constrs, ftype]:
                return t.TypeScheme(vars, t.ConstrainedType(constrs, ftype))

    def type_var_list(self, p):
        return p

    def constr_list(self, p):
        return p

    def constr(self, p):
        return tuple(p)

    def fun_type(self, p):
        match p:
            case [type]:
                return type
            case types:
                return t.FunctionType(types)

    def type_var(self, p):
        return t.TypeVar(p[0])

    def type_const(self, p):
        return t.TypeConstant(p[0])

    def type_app(self, p):
        f, *args = p
        return t.TypeApp(f, args)

    def fix_defn(self, p):
        fixity, prec, operator = p
        return ast.FixitySignature(operator, fixity.type == "INFIXL", int(prec))

    def typeof_defn(self, p):
        name, type = p
        return ast.ValueTypeDefn(name, type)

    def val_defn(self, p):
        match p:
            case [name, value]:
                return ast.ValueDefn(name, value)
            case [name, params, body]:
                return ast.ValueDefn(name, ast.Function(params, body))

    def op_defn(self, p):
        left, op, right, body = p
        return ast.ValueDefn(op, ast.Function([left, right], body))

    def param_list(self, p):
        return p

    def fun_expr(self, p):
        params, body = p
        return ast.Function(params, body)

    def let_expr(self, p):
        *defns, body = p
        return ast.LetExpr(defns, body)

    def match_expr(self, p):
        matchable, *matches = p
        return ast.PatternMatching(matchable, matches)

    def op_chain_expr(self, p):
        match p:
            case [single]:
                return single
            case [left, op, right]:
                return ast.BinaryOperation(left, op, right)
            case chain:
                return ast.OpChain(chain)

    def match(self, p):
        return tuple(p)

    def capture_pattern(self, p):
        return pat.CapturePattern(p[0])

    def data_pattern(self, p):
        match p:
            case [tag]:
                return pat.DataPattern(tag)
            case [tag, names]:
                return pat.DataPattern(
                    tag, [pat.CapturePattern(name) for name in names]
                )

    def literal_pattern(self, p):
        return pat.LiteralPattern(p[0])

    def fun_app(self, p):
        f, args = p
        return ast.FunctionApp(f, args)

    def id_atom(self, p):
        return ast.Id(p[0])

    def expr_list(self, p):
        return p

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
