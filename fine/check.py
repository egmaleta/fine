# TODO: report errors including token's meta

from collections import defaultdict

from . import ast, pattern as pat
from .config import Config
from .type import Quantifier
from .utils import Env, String


type NameEnv = Env[None]


class NameChecker:
    def __init__(self, config: Config):
        self._config = config
        self._quantifier = Quantifier()

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

    def check(self, node: ast.AST, env: NameEnv):
        match node:
            case (
                ast.InternalValue()
                | ast.InternalFunction()
                | ast.Data()
                | ast.PolyData()
                | ast.Int()
                | ast.Float()
                | ast.Unit()
            ):
                pass

            case ast.Id(name):
                self._assert_name(name, env)

            case ast.FunctionApp(f, args):
                self.check(f, env)
                for node in args:
                    self.check(node, env)

            case ast.OpChain(chain):
                for x in chain:
                    if isinstance(x, ast.Expr):
                        self.check(x, env)
                    else:
                        self._assert_name(x, env)

            case ast.LetExpr(defns, body):
                val_names = []
                valtype_names = []
                ops = []
                for defn in defns:
                    match defn:
                        case ast.ValueDefn(name):
                            val_names.append(name)
                        case ast.TypeDefn(name):
                            valtype_names.append(name)
                        case ast.FixitySignature(operators):
                            ops.extend(operators)

                self._assert_unique(val_names)
                self._assert_unique(valtype_names)
                self._assert_unique(ops)

                val_names = set(val_names)
                self._assert_val_defn(ops, val_names)
                self._assert_val_defn(valtype_names, val_names)

                for defn in defns:
                    self.check(defn, env)

                self.check(body, env)

            case ast.PatternMatching(matchable, matches):
                self.check(matchable, env)
                for pattern, expr in matches:
                    match pattern:
                        case pat.LiteralPattern() | pat.DataPattern(_, []):
                            self.check(expr, env)

                        case pat.CapturePattern(name):
                            child_env = env.child_env()
                            child_env.add(name, None)
                            self.check(expr, child_env)

                        case pat.DataPattern(_, capture_patterns):
                            names = [p.name for p in capture_patterns]
                            self._assert_unique(names)

                            child_env = env.child_env()
                            for name in names:
                                child_env.add(name, None)
                            self.check(expr, child_env)

            case ast.Guards(conditionals, fallback):
                for cond, expr in conditionals:
                    self.check(cond, env)
                    self.check(expr, env)

                self.check(fallback, env)

            case ast.Function(params, body):
                self._assert_unique(params)

                child_env = env.child_env()
                for name in params:
                    child_env.add(name, None)

                self.check(body, child_env)

            case ast.ValueDefn(name, value):
                env.add(name, None)
                self.check(value, env)

            case ast.TypeDefn(name, type) as defn:
                defn.type = self._quantifier.quantify(type)

            case ast.DatatypeDefn(_, val_defns, type_defns):
                for defn in val_defns:
                    self.check(defn, env)

                for defn in type_defns:
                    self.check(defn, env)

            case ast.FixitySignature(_, _, prec):
                min_prec = self._config.min_op_precedence
                max_prec = self._config.max_op_precedence

                assert (
                    min_prec <= prec < max_prec
                ), f"Operator precedence ({prec}) is out of the range [{min_prec}, {max_prec})."

            case ast.Module(defns):
                val_names = []
                valtype_names = []
                ops = []
                type_names = []
                ct_names = []
                for defn in defns:
                    match defn:
                        case ast.ValueDefn(name):
                            val_names.append(name)
                        case ast.TypeDefn(name):
                            valtype_names.append(name)
                        case ast.FixitySignature(operators):
                            ops.extend(operators)
                        case ast.DatatypeDefn(type, _, type_defns):
                            type_names.append(type.name)
                            for tdefn in type_defns:
                                ct_names.append(tdefn.name)

                self._assert_unique(val_names)
                self._assert_unique(valtype_names)
                self._assert_unique(ops)
                self._assert_unique(type_names)
                self._assert_unique(ct_names)

                val_names = set(val_names)
                self._assert_val_defn(ops, val_names)
                self._assert_val_defn(valtype_names, val_names)

                for defn in defns:
                    self.check(defn, env)
