from . import ast
from .config import Config
from .utils import Env, String


type SigEnv = Env[tuple[bool, int]]


class Transformer:
    def __init__(self, config: Config):
        self._config = config

    def _binop(self, infixn: list[ast.Expr | String], env: SigEnv):
        rpn: list[ast.Expr | String] = []
        op_stack: list[String] = []

        for item in infixn:
            if not isinstance(item, str):
                rpn.append(item)
                continue

            curr, has_curr = env.get(item)
            curr_prec = curr[1] if has_curr else self._config.default_op_precedence
            is_curr_lassoc = curr[0] if has_curr else self._config.assoc_is_left

            while len(op_stack) > 0:
                top, has_top = env.get(op_stack[-1])
                top_prec = top[1] if has_top else self._config.default_op_precedence

                if top_prec > curr_prec or top_prec == curr_prec and is_curr_lassoc:
                    rpn.append(op_stack.pop())
                else:
                    break

            op_stack.append(item)

        while len(op_stack) > 0:
            rpn.append(op_stack.pop())

        operands: list[ast.Expr] = []
        for item in rpn:
            if not isinstance(item, str):
                operands.append(item)
                continue

            right = operands.pop()
            left = operands.pop()
            operands.append(ast.FunctionApp(ast.FunctionApp(ast.Id(item), left), right))

        assert len(operands) == 1
        return operands[0]

    def _transform(self, node: ast.AST, env: SigEnv):
        match node:
            case (
                ast.InternalValue()
                | ast.InternalFunction()
                | ast.Data()
                | ast.PolyData()
                | ast.Int()
                | ast.Float()
                | ast.Str()
                | ast.Id()
            ):
                return node

            case ast.FunctionApp(f, arg):
                return ast.FunctionApp(
                    self._transform(f, env), self._transform(arg, env)
                )

            case ast.OpChain(chain):
                return self._binop(
                    [
                        (
                            self._transform(item, env)
                            if not isinstance(item, str)
                            else item
                        )
                        for item in chain
                    ],
                    env,
                )

            case ast.Guards(conditionals, fallback):
                return ast.Guards(
                    [
                        (self._transform(cond, env), self._transform(expr, env))
                        for cond, expr in conditionals
                    ],
                    self._transform(fallback, env),
                )

            case ast.Function(params, body):
                return ast.Function(params, self._transform(body, env))

            case ast.PatternMatching(matchable, matches):
                return ast.PatternMatching(
                    self._transform(matchable, env),
                    [(p, self._transform(e, env)) for p, e in matches],
                )

            case ast.LetExpr(defns, body):
                new_env = env.child()
                return ast.LetExpr(
                    [self._transform(defn, new_env) for defn in defns],
                    self._transform(body, new_env),
                )

            case ast.InternalBinding() | ast.InternalDatatype():
                return node

            case ast.Binding(name, value, type):
                return ast.Binding(name, self._transform(value, env), type)

            case ast.Datatype():
                return node

            case ast.FixitySignature(operators, is_left_assoc, prec):
                for op in operators:
                    env.add(op, (is_left_assoc, prec))
                return node

            case ast.Module(defns):
                return ast.Module([self._transform(defn, env) for defn in defns])

            case _:
                node
                assert False

    def transform(self, node: ast.AST):
        return self._transform(node, Env())
