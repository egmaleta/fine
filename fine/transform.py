from . import ast
from .env import Env
from .utils import String


type Sig = tuple[String, bool, int]


class Transformer:
    IS_LEFT_ASSOC = True
    PRECEDENCE = 10

    def _create_binop(self, infixn: list[ast.Expr | String], env: Env[Sig]):
        rpn: list[ast.Expr | String] = []
        op_stack: list[String] = []
        for item in infixn:
            if isinstance(item, ast.Expr):
                rpn.append(item)
                continue

            curr, has_curr = env.get(item)
            curr_prec = curr[2] if has_curr else self.PRECEDENCE
            is_curr_lassoc = curr[1] if has_curr else self.IS_LEFT_ASSOC

            while len(op_stack) > 0:
                top, has_top = env.get(op_stack[-1])
                top_prec = top[2] if has_top else self.PRECEDENCE

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

    def transform(self, node: ast.AST, env: Env[Sig]) -> ast.AST:
        match node:
            case ast.FunctionApp(f, arg):
                return ast.FunctionApp(self.transform(f, env), self.transform(arg, env))

            case ast.OpChain(chain):
                return self._create_binop(
                    [
                        self.transform(el, env) if isinstance(el, ast.Expr) else el
                        for el in chain
                    ],
                    env,
                )

            case ast.BinaryOperation(left, operator, right):
                return ast.BinaryOperation(
                    self.transform(left, env), operator, self.transform(right, env)
                )

            case ast.LetExpr(definitions, body):
                env = env.child_env()
                return ast.LetExpr(
                    [self.transform(defn, env) for defn in definitions],
                    self.transform(body, env),
                )

            case ast.PatternMatching(matchable, matches):
                return ast.PatternMatching(
                    self.transform(matchable, env),
                    [(p, self.transform(e, env)) for p, e in matches],
                )

            case ast.Function(params, body):
                return ast.Function(params, self.transform(body, env))

            case ast.ValueDefn(name, value):
                return ast.ValueDefn(name, self.transform(value, env))

            case ast.DatatypeDefn(type, constructors):
                return ast.DatatypeDefn(
                    type, [(self.transform(defn, env), t) for defn, t in constructors]
                )

            case ast.FixitySignature(op, left_assoc, prec):
                env.add(op, (op, left_assoc, prec))
                return node

            case ast.Module(definitions):
                return ast.Module([self.transform(defn, env) for defn in definitions])

            case _:
                # internal, data, id, literal and typedefn nodes
                return node
