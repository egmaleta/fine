from lark import Transformer, Lark

from . import ast
from .pattern import CapturePattern, DataPattern, LiteralPattern
from .type import TypeConstant, TypeVar, TypeApp, FunctionType, TypeScheme


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
                    FunctionType([*type.args, main_type])
                    if isinstance(type, FunctionType)
                    else FunctionType([type, main_type])
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
        return ast.Module(p[0])

    def defn_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
                return p

    def localdefn_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
                return p

    def int_datatype(self, p):
        match p:
            case [name]:
                return ast.DatatypeDefn(TypeConstant(name))
            case [name, params]:
                return ast.DatatypeDefn(
                    TypeApp(TypeConstant(name), [TypeVar(p) for p in params])
                )

    def datatype(self, p):
        match p:
            case [name, cts]:
                type = TypeConstant(name)
                return _create_datatype_defn(type, cts)

            case [name, params, cts]:
                type = TypeApp(TypeConstant(name), [TypeVar(p) for p in params])
                return _create_datatype_defn(type, cts)

    def typing(self, p):
        name, type = p
        return ast.Typing(name, type)

    def int_binding(self, p):
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

    def int_operation(self, p):
        left, op, right, intr = p
        params = [left, right]
        return ast.Binding(
            op,
            ast.Function(
                params, ast.InternalFunction(intr, [name for name, _ in params])
            ),
        )

    def fixity(self, p):
        fixity, prec, operators = p
        return ast.FixitySignature(operators, fixity.type != "INFIXR", int(prec))

    def binding(self, p):
        match p:
            case [name, value]:
                return ast.Binding(name, value)
            case [name, params, body]:
                return ast.Binding(name, ast.Function(params, body))

    def operation(self, p):
        left, op, right, body = p
        return ast.Binding(op, ast.Function([left, right], body))

    def datact_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
                return p

    def datact(self, p):
        match p:
            case [name]:
                return (name, None)
            case [name, type]:
                return (name, type)

    def type_scheme(self, p):
        match p:
            case [ftype]:
                return ftype
            case [*vars, _, ftype]:
                return TypeScheme(vars, ftype)

    def fun_type(self, p):
        match p:
            case [type]:
                return type
            case types:
                return FunctionType(types)

    def type_var(self, p):
        return TypeVar(p[0])

    def type_const(self, p):
        return TypeConstant(p[0])

    def type_app(self, p):
        f, args = p
        return TypeApp(f, args)

    def targ_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
                return p

    def operator_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
                return p

    def param_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
                return p

    def fun_param_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
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
        defns, body = p
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

    def capture_pattern(self, p):
        return CapturePattern(p[0])

    def data_pattern(self, p):
        match p:
            case [tag]:
                return DataPattern(tag)
            case [tag, names]:
                return DataPattern(tag, [CapturePattern(name) for name in names])

    def literal_pattern(self, p):
        return LiteralPattern(p[0])

    def fun_app(self, p):
        f, args = p
        for arg in args:
            f = ast.FunctionApp(f, arg)
        return f

    def expr_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
                return p

    def match_expr(self, p):
        matchable, matches = p
        return ast.PatternMatching(matchable, matches)

    def match_list(self, p):
        match p:
            case [l, x]:
                l.append(x)
                return l
            case _:
                return p

    def match(self, p):
        return tuple(p)

    def id_atom(self, p):
        return ast.Id(p[0])

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
