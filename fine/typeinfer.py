from dataclasses import dataclass
from collections import deque

from . import ast
from . import names
from . import pattern as pat
from .type import Type, TypeConstant, TypeVar, FunctionType
from .type.quantify import quantify
from .utils import Env


@dataclass
class _Equation:
    left: Type
    right: Type

    def __repr__(self) -> str:
        return f"{self.left} = {self.right}"


def _typename_of_literal(lit: ast.Float | ast.Int | ast.Str):
    match lit:
        case ast.Float():
            return names.FLOAT_TNAME
        case ast.Int():
            return names.INT_TNAME
        case ast.Str():
            return names.STR_TNAME


def _typename_of_literal_pattern(
    lit: pat.FloatPattern | pat.IntPattern | pat.StrPattern,
):
    match lit:
        case pat.FloatPattern():
            return names.FLOAT_TNAME
        case pat.IntPattern():
            return names.INT_TNAME
        case pat.StrPattern():
            return names.STR_TNAME


def _create_ftype(args: list[Type]):
    return quantify(FunctionType(args))


class TypeInferer:
    def __init__(self):
        self._eqs = deque[_Equation]()
        self._unsolved_tvars = set[TypeVar]()
        self._typeconst_env = Env[TypeConstant]()

    def _new_tvar(self):
        tvar = TypeVar(f"t{len(self._unsolved_tvars)}")
        self._unsolved_tvars.add(tvar)
        return tvar

    def _infer(self, node: ast.AST, env: Env[Type]):
        match node:
            case ast.Int() | ast.Float() | ast.Str():
                name = _typename_of_literal(node)
                type, found = self._typeconst_env.get(name)
                assert found

                return type

            case ast.Id(name):
                type, found = env.get(name)
                assert found

                return type

            case ast.FunctionApp(f, arg):
                ftype = self._infer(f, env)
                arg_type = self.infer(arg, env)

                tvar = self._new_tvar()
                eq = _Equation(ftype, FunctionType([arg_type, tvar]))
                self._eqs.append(eq)

                return tvar

            case ast.Guards(conditionals, fallback):
                bool_type, found = self._typeconst_env.get(names.BOOL_TNAME)
                assert found

                branch_types = []
                for cond, expr in conditionals:
                    type = self._infer(cond, env)
                    self._eqs.append(_Equation(type, bool_type))

                    branch_types.append(self._infer(expr, env))

                branch_types.append(self._infer(fallback, env))

                tvar = self._new_tvar()
                eqs = [_Equation(tvar, btype) for btype in branch_types]
                self._eqs.extend(eqs)

                return tvar

            case ast.Function(params, body):
                new_env = env.child()
                types = []
                for name, _ in params:
                    param_type = self._new_tvar()
                    new_env.add(name, param_type)
                    types.append(param_type)

                types.append(self._infer(body, new_env))

                return _create_ftype(types)

            case ast.PatternMatching(matchable, matches):
                mtype = self._infer(matchable, env)

                branch_types = []
                for pattern, expr in matches:
                    match pattern:
                        case pat.CapturePattern(name):
                            new_env = env.child()
                            new_env.add(name, mtype)
                            branch_types.append(self._infer(expr, new_env))

                        case pat.DataPattern(tag):
                            tag_type, found = env.get(tag)
                            assert found
                            self._eqs.append(_Equation(mtype, tag_type))

                            branch_types.append(self._infer(expr, env))

                        case pat.PolyDataPattern(tag, capture_patterns):
                            tag_type, found = env.get(tag)
                            assert found

                            new_env = env.child()
                            types = []
                            for cpattern in capture_patterns:
                                type = self._new_tvar()
                                types.append(type)
                                new_env.add(cpattern.name, type)

                            eq = _Equation(FunctionType([*types, mtype]), tag_type)
                            self._eqs.append(eq)

                            branch_types.append(self._infer(expr, new_env))

                        case _:
                            name = _typename_of_literal_pattern(pattern)
                            type, found = self._typeconst_env.get(name)
                            assert found
                            self._eqs.append(_Equation(mtype, type))

                            branch_types.append(self._infer(expr, env))

                tvar = self._new_tvar()
                eqs = [_Equation(tvar, btype) for btype in branch_types]
                self._eqs.extend(eqs)

                return tvar

            case ast.LetExpr(defns, body):
                new_env = env.child()
                for defn in defns:
                    self._infer(defn, new_env)

                return self._infer(body, new_env)

            case ast.Binding(name, value, type):
                expected_type = type if type is not None else self._new_tvar()
                env.add(name, expected_type)
                inferred_type = self._infer(value, env)

                self._eqs.append(_Equation(expected_type, inferred_type))

            case ast.DatatypeDefn(type, bindings):
                if isinstance(type, TypeConstant):
                    self._typeconst_env.add(type.name, type)

                for binding in bindings:
                    env.add(binding.name, binding.type)

            case ast.FixitySignature():
                pass

            case ast.Module(defns):
                for defn in defns:
                    self._infer(defn, env)

            case _:
                assert False

    def infer(self, node: ast.AST):
        self._infer(node, Env())
