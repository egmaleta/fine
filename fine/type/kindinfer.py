from dataclasses import dataclass
from collections import deque

from ..utils import Env

from . import Type, TypeConstant, TypeVar, TypeApp, TypeScheme
from .kind import Kind, AtomKind, FunctionKind, ATOM


type _Kind = Kind | _KindVar


@dataclass(unsafe_hash=True)
class _KindVar:
    id: int

    def __repr__(self):
        return f"k{self.id}"


@dataclass
class _Equation:
    left: _Kind
    right: _Kind


def _contains(container: _Kind, kvar: _KindVar):
    match container:
        case AtomKind():
            return False

        case FunctionKind(left, right):
            return _contains(left, kvar) or _contains(right, kvar)

        case _:
            return container == kvar


def _subs(target: _Kind, old: _KindVar, new: _Kind):
    match target:
        case AtomKind():
            return target

        case FunctionKind(left, right):
            return FunctionKind(_subs(left, old, new), _subs(right, old, new))

        case _:
            if target == old:
                return new

            return target


class KindInferer:
    def __init__(self):
        self._eqs: deque[_Equation] = deque()
        self._types: list[TypeConstant | TypeVar] = []
        self._unsolved_kvars: set[_KindVar] = set()

    def _next_kvar(self):
        kvar = _KindVar(len(self._unsolved_kvars))
        self._unsolved_kvars.add(kvar)
        return kvar

    def _subs(self, kvar: _KindVar, kind: _Kind):
        for type in self._types:
            type._kind = _subs(type._kind, kvar, kind)

        for eq in self._eqs:
            eq.left = _subs(eq.left, kvar, kind)
            eq.right = _subs(eq.right, kvar, kind)

        self._unsolved_kvars.remove(kvar)

    def _unify(self, k1: _Kind, k2: _Kind):
        if k1 == k2:
            return

        match (k1, k2):
            case (_KindVar() as kvar, rkind):
                if not _contains(rkind, kvar):
                    self._subs(kvar, rkind)
                    return

                assert False  # TODO: recursive subs

            case (lkind, _KindVar() as kvar):
                if not _contains(lkind, kvar):
                    self._subs(kvar, lkind)
                    return

                assert False  # TODO: recursive subs

            case (FunctionKind(), FunctionKind()):
                # FIXME
                self._unify(k1.left, k2.left)
                self._unify(k1.right, k2.right)
                return

        assert False  # TODO: different shapes

    def _solve_eq(self, equation: _Equation):
        self._unify(equation.left, equation.right)

    def _infer(self, type: Type, env: Env[_KindVar | None]):
        match type:
            case TypeVar(name) | TypeConstant(name):
                kvar, found = env.get(name)
                assert found

                if kvar is None:
                    kvar = self._next_kvar()
                    env.set(name, kvar)

                type._kind = kvar
                self._types.append(type)

                return kvar

            case TypeApp(f, args):
                fkind = self._infer(f, env)
                kinds = [self._infer(type_arg, env) for type_arg in args]

                eq = _Equation(fkind, FunctionKind.from_args(kinds))
                self._eqs.append(eq)

                return ATOM

            case TypeScheme(vars, inner):
                new_env = env.child()
                for name in vars:
                    new_env.add(name, None)

                return self._infer(inner, new_env)

            case _:
                assert False

    def infer(self, types: list[Type], env: Env[None]):
        for type in types:
            kind = self._infer(type, env)
            eq = _Equation(kind, ATOM)
            self._eqs.append(eq)

        while len(self._eqs) > 0:
            eq = self._eqs.popleft()
            self._solve_eq(eq)

        for kvar in [*self._unsolved_kvars]:
            self._subs(kvar, ATOM)  # could be any kind
