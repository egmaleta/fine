from collections import defaultdict

from . import ast, pattern as pat
from .type import Quantifier
from .utils import Env, String


type NameEnv = Env[None]


class NameChecker:
    def __init__(self):
        self.quantifier = Quantifier()

    @staticmethod
    def _check_name(name: String, env: NameEnv):
        _, found = env.get(name)
        assert found

    @staticmethod
    def _assert_unique_names(names: list[String]):
        freq: defaultdict[String, list[String]] = defaultdict(lambda: [])
        for name in names:
            freq[name].append(name)

        for repeated_names in freq.values():
            # TODO: better assertion message
            assert len(repeated_names) == 1

    def check(self, node: ast.AST, env: NameEnv):
        match node:
            case (
                ast.InternalValue()
                | ast.InternalFunction()
                | ast.Data()
                | ast.PolyData()
                | ast.NaturalNumber()
                | ast.DecimalNumber()
                | ast.Unit()
            ):
                pass

            case ast.Id(name):
                self._check_name(name, env)

            case ast.FunctionApp(f, args):
                self.check(f, env)
                for node in args:
                    self.check(node, env)

            case ast.OpChain(chain):
                for x in chain:
                    if isinstance(x, ast.Expr):
                        self.check(x, env)
                    else:
                        self._check_name(x, env)

            case ast.BinaryOperation(left, op, right):
                self.check(left, env)
                self._check_name(op, env)
                self.check(right, env)

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
                        case ast.FixitySignature(op):
                            ops.append(op)
                        case _:
                            assert False

                self._assert_unique_names(val_names)
                self._assert_unique_names(valtype_names)
                self._assert_unique_names(ops)

                val_names = set(val_names)

                ops = set(ops)
                # TODO: better assertion message
                assert len(ops - val_names) == 0

                valtype_names = set(valtype_names)
                # TODO: better assertion message
                assert len(valtype_names - val_names) == 0

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
                            self._assert_unique_names(names)

                            child_env = env.child_env()
                            for name in names:
                                child_env.add(name, None)
                            self.check(expr, child_env)

            case ast.Function(params, body):
                self._assert_unique_names(params)

                child_env = env.child_env()
                for name in params:
                    child_env.add(name, None)

                self.check(body, child_env)

            case ast.ValueDefn(name, value):
                env.add(name, None)
                self.check(value, env)

            case ast.TypeDefn(_, type) as defn:
                defn.type = self.quantifier.quantify(type)

            case ast.DatatypeDefn(type, val_defns, type_defns):
                for defn in val_defns:
                    self.check(defn, env)
                for defn in type_defns:
                    self.check(defn, env)

            case ast.FixitySignature(_, _, prec):
                assert 0 <= prec < 10

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
                        case ast.FixitySignature(op):
                            ops.append(op)
                        case ast.DatatypeDefn(type, _, type_defns):
                            type_names.append(type.name)
                            for tdefn in type_defns:
                                ct_names.append(tdefn.name)
                        case _:
                            assert False

                self._assert_unique_names(val_names)
                self._assert_unique_names(valtype_names)
                self._assert_unique_names(ops)
                self._assert_unique_names(type_names)
                self._assert_unique_names(ct_names)

                val_names = set(val_names)

                ops = set(ops)
                # TODO: better assertion message
                assert len(ops - val_names) == 0

                valtype_names = set(valtype_names)
                # TODO: better assertion message
                assert len(valtype_names - val_names) == 0

                for defn in defns:
                    self.check(defn, env)
