from dataclasses import dataclass

from . import ast
from . import pattern as pat
from .utils import Env, String


@dataclass
class Closure[T]:
    f: ast.Function
    env: Env[T]


@dataclass
class Lazy[T]:
    expr: ast.Expr
    env: Env[T]


@dataclass
class PolyData[T]:
    tag: String
    values: list[T]


type Value = (
    PolyData[Value]
    | Closure[Value]
    | Lazy[Value]
    | ast.Int
    | ast.Float
    | ast.Str
    | ast.Data
)


class Evaluator:
    def __init__(self, internals: dict[String]):
        self._internals = internals

    def _unlazy(self, value: Value):
        if isinstance(value, Lazy):
            return self._eval(value.expr, value.env)

        return value

    def _lazy_eval(self, node: ast.Expr, env: Env[Value]):
        match node:
            case ast.Data() | ast.Int() | ast.Float() | ast.Str():
                return node

            case ast.Id(name):
                return env.get(name)[0]

            case ast.Function() as f:
                return Closure(f, env)

            case _:
                return Lazy(node, env)

    def _eval(self, node: ast.AST, env: Env[Value]) -> Value:
        match node:
            case ast.InternalValue(name):
                assert name in self._internals
                return self._internals[name]

            case ast.InternalFunction(name, arg_names):
                assert name in self._internals

                f = self._internals[name]
                args = [self._unlazy(env.get(name)[0]) for name in arg_names]
                return f(*args)

            case ast.Data():
                return node

            case ast.PolyData(tag, value_names):
                values = [self._unlazy(env.get(name)[0]) for name in value_names]
                return PolyData(tag, values)

            case ast.Int() | ast.Float() | ast.Str():
                return node

            case ast.Id(name):
                return self._unlazy(env.get(name)[0])

            case ast.FunctionApp(f, arg):
                cl = self._eval(f, env)
                assert isinstance(cl, Closure)

                param, *rest = cl.f.params

                new_env = cl.env.child()
                name, is_lazy = param
                new_env.add(
                    name, self._lazy_eval(arg, env) if is_lazy else self._eval(arg, env)
                )

                # full app
                if len(rest) == 0:
                    return self._eval(cl.f.body, new_env)

                # partial app
                return Closure(ast.Function(rest, cl.f.body), new_env)

            case ast.Guards(conditionals, fallback):
                for cond, expr in conditionals:
                    data = self._eval(cond, env)
                    assert isinstance(data, ast.Data)
                    if data.tag == "True":
                        return self._eval(expr, env)

                return self._eval(fallback, env)

            case ast.Function() as f:
                return Closure(f, env)

            case ast.PatternMatching(matchable, matches):
                value = self._eval(matchable, env)

                for pattern, expr in matches:
                    match pattern:
                        case pat.CapturePattern(name):
                            new_env = env.child()
                            new_env.add(name, value)
                            return self._eval(expr, new_env)

                        case pat.DataPattern(tag):
                            if isinstance(value, ast.Data) and value.tag == tag:
                                return self._eval(expr, env)

                        case pat.PolyDataPattern(tag, capture_patterns):
                            if isinstance(value, PolyData) and value.tag == tag:
                                new_env = env.child()
                                for p, v in zip(capture_patterns, value.values):
                                    new_env.add(p.name, v)
                                return self._eval(expr, new_env)

                        case (
                            pat.FloatPattern(pat_value)
                            | pat.IntPattern(pat_value)
                            | pat.StrPattern(pat_value)
                        ):
                            if (
                                isinstance(value, (ast.Int, ast.Float, ast.Str))
                                and value.value == pat_value
                            ):
                                return self._eval(expr, env)

                assert False, "No pattern was matched"

            case ast.LetExpr(defns, body):
                new_env = env.child()
                for defn in defns:
                    self._eval(defn, new_env)

                return self._eval(body, new_env)

            case ast.Binding(name, value):
                env.add(name, self._eval(value, env))

            case ast.Datatype(_, bindings):
                for binding in bindings:
                    self._eval(binding, env)

            case ast.FixitySignature():
                pass

            case ast.Module(defns):
                for defn in defns:
                    self._eval(defn, env)

            case _:
                False

    def eval(self, node: ast.Module):
        env = Env()
        self._eval(node, env)
        return env


def try_pythonize(value: Value):
    match value:
        case ast.Int(v):
            return int(v)

        case ast.Float(v):
            return float(v)

        case ast.Str(v):
            return v[1:-1].encode().decode("unicode_escape")

        case ast.Data(tag) as data:
            match tag:
                case "True":
                    return True
                case "False":
                    return False
                case "Unit":
                    return ()
                case "Nil":
                    return []

            return data

        case PolyData(tag, values) as data:
            if tag == "Cons":
                assert len(values) == 2
                head, tail = [try_pythonize(v) for v in values]
                return [head, *tail]

            return data

    return value
