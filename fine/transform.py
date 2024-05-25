from lark.lexer import Token

from . import ast
from .utils import Scope


class Transformer:
    IS_LEFT_ASSOC = True
    PRECEDENCE = 10

    def _create_binop(
        self, infixn: list[ast.Expr | Token], scope: Scope[str, ast.FixitySignature]
    ) -> ast.BinaryOperation:
        rpn: list[ast.Expr | Token] = []
        op_stack: list[Token] = []
        for item in infixn:
            if isinstance(item, ast.Expr):
                rpn.append(item)
                continue

            curr, has_curr = scope.get(item)
            curr_prec = curr.precedence if has_curr else self.PRECEDENCE
            is_curr_lassoc = (
                curr.is_left_associative if has_curr else self.IS_LEFT_ASSOC
            )

            while len(op_stack) > 0:
                top, has_top = scope.get(op_stack[-1])
                top_prec = top.precedence if has_top else self.PRECEDENCE

                if top_prec > curr_prec or top_prec == curr_prec and is_curr_lassoc:
                    rpn.append(op_stack.pop())
                else:
                    break

            op_stack.append(item)

        while len(op_stack) > 0:
            rpn.append(op_stack.pop())

        operands: list[ast.Expr] = []
        for item in rpn:
            if isinstance(item, ast.Expr):
                operands.append(item)
                continue

            right = operands.pop()
            left = operands.pop()
            operands.append(ast.BinaryOperation(left, item, right))

        assert len(operands) == 1
        return operands[0]

    def transform(
        self, node: ast.AST, scope: Scope[str, ast.FixitySignature]
    ) -> ast.AST:
        match node:
            case ast.FunctionApp(f, arg):
                return ast.FunctionApp(
                    self.transform(f, scope), self.transform(arg, scope)
                )

            case ast.OpChain(chain):
                return self._create_binop(
                    [
                        self.transform(el, scope) if isinstance(el, ast.Expr) else el
                        for el in chain
                    ],
                    scope,
                )

            case ast.BinaryOperation(left, operator, right):
                return ast.BinaryOperation(
                    self.transform(left, scope), operator, self.transform(right, scope)
                )

            case ast.LetExpr(definitions, body):
                scope = scope.new_scope()
                return ast.LetExpr(
                    [self.transform(defn, scope) for defn in definitions],
                    self.transform(body, scope),
                )

            case ast.PatternMatching(matchable, matches):
                return ast.PatternMatching(
                    self.transform(matchable, scope),
                    [(p, self.transform(e, scope)) for p, e in matches],
                )

            case ast.MultiFunction(params, body):
                f = self.transform(body, scope)
                for p in reversed(params):
                    f = ast.Function(p, f)
                return f

            case ast.Function(param, body):
                return ast.Function(param, self.transform(body, scope))

            case ast.ValueDefn(name, value):
                return ast.ValueDefn(name, self.transform(value, scope))

            case ast.DatatypeDefn(type, constructors):
                return ast.DatatypeDefn(
                    type, [self.transform(ct, scope) for ct in constructors]
                )

            case ast.FixitySignature(op):
                scope.set(op, node)
                return node

            case ast.Module(definitions):
                return ast.Module([self.transform(defn, scope) for defn in definitions])

            case _:
                # internal, data, id, literal and typedefn nodes
                return node
