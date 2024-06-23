from collections import defaultdict

from . import ast
from . import pattern as pat
from .config import Config
from .type.quantify import quantify
from .utils import Env, String


type NameEnv = Env[None]


class SemanticChecker:
    def __init__(self, config: Config):
        self._config = config

    def _assert_name(self, name: String, env: NameEnv):
        if name == self._config.ignore_name:
            return

        _, found = env.get(name)
        assert found, f"Value bound to '{name}' not found in scope."

    def _assert_unique(self, names: list[String]):
        freq: defaultdict[String, list[String]] = defaultdict(lambda: [])
        for name in names:
            if name == self._config.ignore_name:
                continue

            freq[name].append(name)

        for repeated_names in freq.values():
            assert (
                len(repeated_names) == 1
            ), f"Multiple definitions bound to the same name '{repeated_names[0]}'."

    def _assert_val_defn(self, names: list[String], val_names: set[String]):
        for name in set(names) - val_names:
            assert False, f"Missing value definition for '{name}'."

    def _check(self, node: ast.AST, env: NameEnv):
        match node:
            case (
                ast.InternalValue()
                | ast.InternalFunction()
                | ast.Data()
                | ast.PolyData()
                | ast.Int()
                | ast.Float()
                | ast.Str()
            ):
                pass

            case ast.Id(name):
                self._assert_name(name, env)

            case ast.FunctionApp(f, arg):
                self._check(f, env)
                self._check(arg, env)

            case ast.OpChain(chain):
                for item in chain:
                    if not isinstance(item, str):
                        self._check(item, env)
                    else:
                        self._assert_name(item, env)

            case ast.Guards(conditionals, fallback):
                for cond, expr in conditionals:
                    self._check(cond, env)
                    self._check(expr, env)

                self._check(fallback, env)

            case ast.Function(params, body):
                names = [name for name, _ in params]
                self._assert_unique(names)

                new_env = env.child()
                for name in names:
                    new_env.add(name, None)

                self._check(body, new_env)

            case ast.PatternMatching(matchable, matches):
                self._check(matchable, env)
                for pattern, expr in matches:
                    match pattern:
                        case pat.CapturePattern(name):
                            new_env = env.child()
                            new_env.add(name, None)
                            self._check(expr, new_env)

                        case pat.PolyDataPattern(_, capture_patterns):
                            names = [p.name for p in capture_patterns]
                            self._assert_unique(names)

                            new_env = env.child()
                            for name in names:
                                new_env.add(name, None)
                            self._check(expr, new_env)

                        case _:
                            self._check(expr, env)

            case ast.LetExpr(defns, body):
                self._assert_unique([defn.name for defn in defns])

                for defn in defns:
                    self._check(defn, env)

                self._check(body, env)

            case ast.Binding(name, value, type):
                env.add(name, None)
                self._check(value, env)
                if type is not None:
                    node.type = quantify(type)

            case ast.DatatypeDefn(_, bindings):
                for binding in bindings:
                    self._check(binding, env)

            case ast.FixitySignature(_, _, prec):
                min_prec = self._config.min_op_precedence
                max_prec = self._config.max_op_precedence

                assert (
                    min_prec <= prec < max_prec
                ), f"Operator precedence ({prec}) is out of the range [{min_prec}, {max_prec})."

            case ast.Module(defns):
                val_names = []
                ops = []
                type_names = []
                ct_names = []
                for defn in defns:
                    match defn:
                        case ast.Binding(name):
                            val_names.append(name)
                        case ast.FixitySignature(operators):
                            ops.extend(operators)
                        case ast.DatatypeDefn(type, bindings):
                            type_names.append(type.name)
                            for binding in bindings:
                                ct_names.append(binding.name)
                        case _:
                            assert False

                self._assert_unique(val_names)
                self._assert_unique(ops)
                self._assert_unique(type_names)
                self._assert_unique(ct_names)

                self._assert_val_defn(ops, set(val_names))

                for defn in defns:
                    self._check(defn, env)

            case _:
                assert False

    def check(self, node: ast.AST):
        self._check(node, Env())
