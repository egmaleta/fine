from dataclasses import dataclass

from . import ast, pattern as pat
from .config import Config
from .utils import Env, String


@dataclass
class Closure[T]:
    f: ast.Function
    env: Env[T]


@dataclass
class PolyData[T]:
    tag: String
    values: list[T]


type Value = ast.Int | ast.Float | ast.Unit | ast.Data | PolyData[Value] | Closure[
    Value
]


class Evaluator:
    def __init__(self, internals: dict[String], config: Config):
        self._internals = internals
        self._config = config

    @staticmethod
    def try_pythonize(value: Value):
        match value:
            case ast.Int(value):
                return int(value)

            case ast.Float(value):
                return float(value)

            case ast.Unit():
                return ()

            case ast.Data(tag) as data:
                match tag:
                    case "True":
                        return True
                    case "False":
                        return False
                    case "Nil":
                        return []

                return data

            case PolyData(tag, values) as data:
                if tag == "Cons":
                    assert len(values) == 2
                    head, tail = [Evaluator.try_pythonize(v) for v in values]
                    return [head, *tail]

                return data

        return value

    def _eval_closure(self, cl: Closure[Value], args: list[ast.Expr], env: Env[Value]):
        params = cl.f.params
        child_env = cl.env.child_env()
        for arg, param in zip(args, params):
            arg = self._eval(arg, env)
            child_env.add(param, arg)

        args_len = len(args)
        params_len = len(params)

        # partial app
        if args_len < params_len:
            return Closure(ast.Function(params[args_len:], cl.f.body), child_env)

        value = self._eval(cl.f.body, child_env)

        # full app
        if args_len == params_len:
            return value

        # 'value' must be a closure
        assert isinstance(value, Closure)
        return self._eval_closure(value, args[params_len:], env)

    def _eval(self, node: ast.AST, env: Env[Value]) -> Value:
        match node:
            case ast.InternalValue(name):
                assert name in self._internals
                return self._internals[name]

            case ast.InternalFunction(name, arg_names):
                assert name in self._internals

                f = self._internals[name]
                args = [env.get(name)[0] for name in arg_names]
                return f(*args)

            case ast.Data():
                return node

            case ast.PolyData(tag, value_names):
                values = [env.get(name)[0] for name in value_names]
                return PolyData(tag, values)

            case ast.Int() | ast.Float() | ast.Unit():
                return node

            case ast.Id(name):
                return env.get(name)[0]

            case ast.FunctionApp(f, args):
                cl = self._eval(f, env)
                assert isinstance(cl, Closure)

                return self._eval_closure(cl, args, env)

            case ast.LetExpr(defns, body):
                child_env = env.child_env()
                for defn in defns:
                    self._eval(defn, child_env)

                return self._eval(body, child_env)

            case ast.PatternMatching(matchable, matches):
                value = self._eval(matchable, env)

                for pattern, expr in matches:
                    match pattern:
                        case pat.LiteralPattern(pat_value):
                            if (
                                isinstance(value, (ast.Int, ast.Float, ast.Unit))
                                and value.value == pat_value
                            ):
                                return self._eval(expr, env)

                        case pat.DataPattern(tag, []):
                            if isinstance(value, ast.Data) and value.tag == tag:
                                return self._eval(expr, env)

                        case pat.DataPattern(tag, capture_patterns):
                            if isinstance(value, PolyData) and value.tag == tag:
                                child_env = env.child_env()
                                for p, v in zip(capture_patterns, value.values):
                                    child_env.add(p.name, v)
                                return self._eval(expr, child_env)

                        case pat.CapturePattern(name):
                            child_env = env.child_env()
                            child_env.add(name, value)
                            return self._eval(expr, child_env)

                assert False, "No pattern was matched"

            case ast.Guards(conditionals, fallback):
                for cond, expr in conditionals:
                    data = self._eval(cond, env)
                    assert isinstance(data, ast.Data)
                    if data.tag == "True":
                        return self._eval(expr, env)

                return self._eval(fallback, env)

            case ast.Function() as f:
                return Closure(f, env)

            case ast.ValueDefn(name, value):
                env.add(name, self._eval(value, env))

            case ast.TypeDefn():
                pass

            case ast.DatatypeDefn(_, val_defns, _):
                for defn in val_defns:
                    self._eval(defn, env)

            case ast.FixitySignature():
                pass

            case ast.Module(defns):
                for defn in defns:
                    self._eval(defn, env)

    def eval(self, node: ast.Defn, env: Env[Value], entrypoint: String):
        self._eval(node, env)

        value = env.get(entrypoint)[0]
        return self.try_pythonize(value)
