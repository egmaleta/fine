from . import ast
from .config import Config
from .utils import Env, String


type SigEnv = Env[ast.FixitySignature]


class Transformer:
    def __init__(self, config: Config):
        self._config = config

    def _binop(self, infixn: list[ast.Expr | String], env: SigEnv):
        rpn: list[ast.Expr | String] = []
        op_stack: list[String] = []

        for item in infixn:
            if isinstance(item, ast.Expr):
                rpn.append(item)
                continue

            curr, has_curr = env.get(item)
            curr_prec = (
                curr.precedence if has_curr else self._config.default_op_precedence
            )
            is_curr_lassoc = (
                curr.is_left_associative if has_curr else self._config.assoc_is_left
            )

            while len(op_stack) > 0:
                top, has_top = env.get(op_stack[-1])
                top_prec = (
                    top.precedence if has_top else self._config.default_op_precedence
                )

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
            operands.append(ast.FunctionApp(ast.Id(item), [left, right]))

        assert len(operands) == 1
        return operands[0]

    def transform(self, node: ast.AST, env: SigEnv):
        match node:
            case ast.FunctionApp(f, args):
                return ast.FunctionApp(
                    self.transform(f, env), [self.transform(arg, env) for arg in args]
                )

            case ast.OpChain(chain):
                return self._binop(
                    [
                        self.transform(el, env) if isinstance(el, ast.Expr) else el
                        for el in chain
                    ],
                    env,
                )

            case ast.LetExpr(defns, body):
                child_env = env.child_env()
                return ast.LetExpr(
                    [self.transform(defn, child_env) for defn in defns],
                    self.transform(body, child_env),
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

            case ast.FixitySignature(op) as fs:
                env.add(op, fs)
                return node

            case ast.Module(defns):
                return ast.Module([self.transform(defn, env) for defn in defns])

            case _:
                return node
