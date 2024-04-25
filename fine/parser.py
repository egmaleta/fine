from lark import Transformer, Lark

from . import ast


class ASTBuilder(Transformer):
    def module(self, p):
        defn_list = []
        for defn in p:
            # fixity signatures
            if isinstance(defn, list):
                defn_list.extend(defn)
            else:
                defn_list.append(defn)

        return ast.Module(defn_list)

    def external_value_defn(self, p):
        name, id = p
        return ast.ValueDefn(name, ast.ExternalExpr(id.value))

    def external_func_defn(self, p):
        name, params, id = p
        return ast.ValueDefn(
            name,
            ast.Function(
                params, ast.ExternalFunction(id.value, [p.value for p in params])
            ),
        )

    def external_op_defn(self, p):
        left, name, right, id = p
        params = [left, right]
        return ast.ValueDefn(
            name,
            ast.Function(
                params, ast.ExternalFunction(id.value, [p.value for p in params])
            ),
        )

    def external(self, p):
        return p[0]

    def value_defn(self, p):
        name, value = p
        return ast.ValueDefn(name, value)

    def func_defn(self, p):
        name, params, value = p
        return ast.ValueDefn(name, ast.Function(params, value))

    def op_defn(self, p):
        left, name, right, value = p
        params = [left, right]
        return ast.ValueDefn(name, ast.Function(params, value))

    def fixity_defn(self, p):
        print(p)
        fixity, prec, *operators = p
        is_left_assoc = fixity.type == "INFIXL"
        prec = int(prec)

        return [ast.FixitySignature(op, is_left_assoc, prec) for op in operators]

    def params(self, p):
        return p

    def name(self, p):
        return p[0]

    def func_expr(self, p):
        if len(p) > 1:
            return ast.Function(p[0], p[1])
        return ast.Function([], p[0])

    def block_expr(self, p):
        return ast.Block(p[0], p[1])

    def let_expr(self, p):
        *definitions, expr = p
        for defn in definitions[::-1]:
            expr = ast.LetExpr(defn, expr)

        return expr

    def match_expr(self, p):
        return ast.PatternMatching(p[0], p[1])

    def cond_expr(self, p):
        return ast.Conditional(p[0], p[1], p[2])

    def actions(self, p):
        if len(p) == 1:
            return [p[0]]

        return [p[0], *p[1]]

    def matches(self, p):
        if len(p) == 2:
            return [(p[0], p[1])]

        return [(p[0], p[1]), *p[2]]

    def id_pattern(self, p):
        return ast.Identifier(p[0])

    def ct_pattern(self, p):
        return ast.Data(p[0])

    def op_chain(self, p):
        if len(p) == 1:
            return p[0]

        operand, op, rest = p
        elements = [operand, op]
        if isinstance(rest, ast.OpChain):
            elements.extend(rest.elements)
        else:
            elements.append(rest)

        return ast.OpChain(elements)

    def operator(self, p):
        return p[0]

    def func_app(self, p):
        target, arg = p
        return ast.FunctionApp(target, arg)

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
    transformer=ASTBuilder(),
)


def parse(text: str) -> ast.Module:
    return PARSER.parse(text)
