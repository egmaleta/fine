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
    def _create_datatype_defn(main_type, pairs):
        val_defns = []
        type_defns = []
        for name, type in pairs:
            match type:
                case None:
                    val_defns.append(ast.ValueDefn(name, ast.Data(name)))
                    type_defns.append(ast.TypeDefn(name, main_type))

                case _:
                    ftype = (
                        t.FunctionType([*type.args, main_type])
                        if isinstance(type, t.FunctionType)
                        else t.FunctionType([type, main_type])
                    )
                    params = [f"_{i+1}" for i in range(len(ftype) - 1)]

                    val_defns.append(
                        ast.ValueDefn(
                            name, ast.Function(params, ast.PolyData(name, params))
                        )
                    )
                    type_defns.append(ast.TypeDefn(name, ftype))

        return ast.DatatypeDefn(main_type, val_defns, type_defns)

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

    def quant_type(self, p):
        match p:
            case [ftype]:
                return ftype
            case [vars, _, ftype]:
                return t.TypeScheme(vars, ftype)

    def type_var_list(self, p):
        return p

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
        fixity, prec, *operators = p
        return ast.FixitySignature(operators, fixity.type != "INFIXR", int(prec))

    def typeof_defn(self, p):
        name, type = p
        return ast.TypeDefn(name, type)

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

    def guard_expr(self, p):
        *exprs, fallback = p
        conditionals = [(exprs[i], exprs[i + 1]) for i in range(0, len(exprs) - 1, 2)]
        return ast.Guards(conditionals, fallback)

    def op_chain_expr(self, p):
        match p:
            case [single]:
                return single
            case [left, op, right]:
                return ast.FunctionApp(ast.Id(op), [left, right])
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

    def match_expr(self, p):
        matchable, *matches = p
        return ast.PatternMatching(matchable, matches)

    def expr_list(self, p):
        return p

    def dec_literal(self, p):
        return ast.Float(p[0])

    def nat_literal(self, p):
        return ast.Int(p[0])

    def unit_literal(self, p):
        return ast.Unit(p[0])

    def string_literal(self, p):
        return ast.Str(p[0])


PARSER = Lark.open(
    "fine.lark",
    start="module",
    parser="lalr",
    lexer="basic",
    transformer=ASTBuilder(),
)


def parse(text: str) -> ast.Module:
    return PARSER.parse(text)
