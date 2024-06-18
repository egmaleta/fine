from dataclasses import dataclass
from collections import deque

from ..utils import Env

from . import kind as k, type as t


@dataclass(unsafe_hash=True)
class _KindVar(k.Kind):
    id: int


@dataclass
class _Equation:
    left: k.Kind
    right: k.Kind


def _contains(container: k.Kind, kvar: _KindVar):
    match container:
        case k.AtomKind():
            return False

        case k.FunctionKind(args):
            return any(_contains(type_arg, kvar) for type_arg in args)

        case _:
            return container == kvar


def _subs(target: k.Kind, old: _KindVar, new: k.Kind):
    match target:
        case k.AtomKind():
            return target

        case k.FunctionKind(args):
            return k.FunctionKind([_subs(kind_arg, old, new) for kind_arg in args])

        case _:
            if target == old:
                return new

            return target


class KindInferer:
    def __init__(self):
        self._eqs: deque[_Equation] = deque()
        self._types: list[t.TypeConstant | t.TypeVar] = []
        self._unsolved_kvars: set[_KindVar] = set()

    def _next_kvar(self):
        kvar = _KindVar(len(self._unsolved_kvars))
        self._unsolved_kvars.add(kvar)
        return kvar

    def _subs(self, kvar: _KindVar, kind: k.Kind):
        for type in self._types:
            type._kind = _subs(type._kind, kvar, kind)

        for eq in self._eqs:
            eq.left = _subs(eq.left, kvar, kind)
            eq.right = _subs(eq.right, kvar, kind)

        self._unsolved_kvars.remove(kvar)

    def _unify(self, k1: k.Kind, k2: k.Kind):
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

            case (k.FunctionKind(), k.FunctionKind()):
                # FIXME
                self._unify(k1.left, k2.left)
                self._unify(k1.right, k2.right)
                return

        assert False  # TODO: different shapes

    def _solve_eq(self, equation: _Equation):
        self._unify(equation.left, equation.right)

    def _infer(self, type: t.Type, env: Env[_KindVar | None]):
        match type:
            case t.TypeVar(name) | t.TypeConstant(name):
                kvar, found = env.get(name)
                assert found

                if kvar is None:
                    kvar = self._next_kvar()
                    env.set(name, kvar)

                type._kind = kvar
                self._types.append(type)

                return kvar

            case t.TypeApp(f, args):
                fkind = self._infer(f, env)
                kinds = [self._infer(type_arg, env) for type_arg in args]

                eq = _Equation(fkind, k.FunctionKind([*kinds, k.ATOM_KIND]))
                self._eqs.append(eq)

                return k.ATOM_KIND

            case t.FunctionType(args):
                eqs = [
                    _Equation(self._infer(type_arg, env), k.ATOM_KIND)
                    for type_arg in args
                ]
                self._eqs.extend(eqs)

                return k.ATOM_KIND

            case t.TypeScheme(vars, inner):
                new_env = env.child()
                for name in vars:
                    new_env.add(name, None)

                return self._infer(inner, new_env)

            case _:
                assert False

    def infer(self, types: list[t.Type], env: Env[None]):
        for type in types:
            kind = self._infer(type, env)
            eq = _Equation(kind, k.ATOM_KIND)
            self._eqs.append(eq)

        while len(self._eqs) > 0:
            eq = self._eqs.popleft()
            self._solve_eq(eq)

        for kvar in [*self._unsolved_kvars]:
            self._subs(kvar, k.ATOM_KIND)  # could be any kind
