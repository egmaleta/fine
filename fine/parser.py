from lark import Transformer, Lark

from . import ast
from . import pattern as pat
from . import type as t


def _create_function_app(f, args):
    match args:
        case [arg, *rest]:
            return _create_function_app(ast.FunctionApp(f, arg), rest)
        case []:
            return f


def _create_datatype_defn(main_type, pairs):
    bindings = []
    typings = []
    for name, type in pairs:
        match type:
            case None:
                bindings.append(ast.Binding(name, ast.Data(name)))
                typings.append(ast.Typing(name, main_type))

            case _:
                ftype = (
                    t.FunctionType([*type.args, main_type])
                    if isinstance(type, t.FunctionType)
                    else t.FunctionType([type, main_type])
                )
                params = [(f"_{i+1}", False) for i in range(len(ftype) - 1)]

                bindings.append(
                    ast.Binding(
                        name,
                        ast.Function(
                            params, ast.PolyData(name, [name for name, _ in params])
                        ),
                    )
                )
                typings.append(ast.Typing(name, ftype))

    return ast.DatatypeDefn(main_type, bindings, typings)


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

    def data_defn(self, p):
        match p:
            case [name, cts]:
                type = t.TypeConstant(name)
                return _create_datatype_defn(type, cts)

            case [name, params, cts]:
                type = t.TypeApp(t.TypeConstant(name), [t.TypeVar(p) for p in params])
                return _create_datatype_defn(type, cts)

    def int_val_defn(self, p):
        match p:
            case [name, intr]:
                return ast.Binding(name, ast.InternalValue(intr))
            case [name, params, intr]:
                return ast.Binding(
                    name,
                    ast.Function(
                        params, ast.InternalFunction(intr, [name for name, _ in params])
                    ),
                )

    def int_op_defn(self, p):
        left, op, right, intr = p
        params = [left, right]
        return ast.Binding(
            op,
            ast.Function(
                params, ast.InternalFunction(intr, [name for name, _ in params])
            ),
        )

    def fix_defn(self, p):
        fixity, prec, *operators = p
        return ast.FixitySignature(operators, fixity.type != "INFIXR", int(prec))

    def typeof_defn(self, p):
        name, type = p
        return ast.Typing(name, type)

    def val_defn(self, p):
        match p:
            case [name, value]:
                return ast.Binding(name, value)
            case [name, params, body]:
                return ast.Binding(name, ast.Function(params, body))

    def op_defn(self, p):
        left, op, right, body = p
        return ast.Binding(op, ast.Function([left, right], body))

    def datact_list(self, p):
        return p

    def datact(self, p):
        match p:
            case [ct]:
                return (ct, None)
            case [ct, type]:
                return (ct, type)

    def type_scheme(self, p):
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

    def param_list(self, p):
        return p

    def fun_param_list(self, p):
        return p

    def fun_param(self, p):
        match p:
            case [_, name]:
                return (name, True)
            case [name]:
                return (name, False)

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
                return ast.FunctionApp(ast.FunctionApp(ast.Id(op), left), right)
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
        return _create_function_app(f, args)

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
