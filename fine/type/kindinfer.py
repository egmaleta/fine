from dataclasses import dataclass

from ..utils import String

from .type import *


def _assign(type: TypeVar | TypeConstant, kind: Kind, env: KindEnv):
    type._kind = kind
    assert env.set(type.name, kind)


def _kindof(type: TypeVar | TypeConstant, env: KindEnv):
    kind, found = env.get(type.name)
    assert found

    if kind is not None and type._kind is None:
        type._kind = kind

    return type._kind


@dataclass
class _Equation:
    left: TypeConstant | TypeVar
    right: list[Kind | TypeConstant | TypeVar]
    env: KindEnv

    def __post_init__(self):
        _, found = self.env.get(self.left.name)
        assert found

    def solved(self):
        lkind = _kindof(self.left, self.env)
        if lkind is not None:
            for item in self.right:
                assert isinstance(lkind, FunctionKind)

                if not isinstance(item, Kind) and _kindof(item, self.env) is None:
                    _assign(item, lkind.left, self.env)

                lkind = lkind.right

            return True

        new_right = []
        all_solved = True
        for item in self.right:
            if isinstance(item, Kind):
                new_right.append(item)
                continue

            kind = _kindof(item, self.env)
            if kind is not None:
                new_right.append(kind)
                continue

            all_solved = False
            new_right.append(item)

        if all_solved:
            rkind = FunctionKind([*new_right, ATOM_KIND])
            _assign(self.left, rkind, self.env)

            return True

        self.right = new_right
        return False


class KindInferer:
    def __init__(self):
        self._equations: list[_Equation] = []
        self._tvars: list[TypeVar] = []

    def _infer(self, type: Type, env: KindEnv):
        match type:
            case TypeConstant():
                return _kindof(type, env)

            case TypeVar():
                self._tvars.append(type)
                return _kindof(type, env)

            case TypeApp(f, args):
                fkind = self._infer(f, env)

                if fkind is None:
                    items = []
                    all_kinds = True
                    for type_arg in args:
                        kind = self._infer(type_arg, env)
                        if kind is not None:
                            items.append(kind)
                            continue

                        all_kinds = False
                        items.append(type_arg)

                    if all_kinds:
                        _assign(f, FunctionKind([*items, ATOM_KIND]), env)
                    else:
                        eq = _Equation(f, items, env)
                        self._equations.append(eq)

                else:
                    for type_arg in args:
                        assert isinstance(fkind, FunctionKind)
                        lkind = fkind.left

                        kind = self._infer(type_arg, env)
                        if kind is None:
                            _assign(type_arg, lkind, env)

                        fkind = fkind.right

                return ATOM_KIND

            case FunctionType() as ftype:
                # kind(->) == * -> *
                for type_arg in [ftype.left, ftype.right]:
                    kind = self._infer(type_arg, env)
                    if kind is None:
                        _assign(type_arg, ATOM_KIND, env)

                return ATOM_KIND

            case TypeScheme(vars, inner):
                new_env = env.child_env()
                for name in vars:
                    new_env.add(name, None)

                kind = self._infer(inner, new_env)
                if kind is None:
                    _assign(inner, ATOM_KIND, new_env)

                return ATOM_KIND

    def infer(self, types: list[Type], env: KindEnv):
        for type in types:
            kind = self._infer(type, env)
            if kind is None:
                _assign(type, ATOM_KIND, env)

        leftside_types = [eq.left for eq in self._equations]
        while True:
            prev_len = len(self._equations)

            self._equations = [eq for eq in self._equations if not eq.solved()]
            new_len = len(self._equations)

            if new_len == 0:
                return

            if new_len < prev_len:
                continue

            for tvar in self._tvars:
                if tvar not in leftside_types:
                    for eq in self._equations:
                        kind, found = eq.env.get(tvar.name)
                        if found and kind is None:
                            _assign(tvar, ATOM_KIND, eq.env)
                    self._tvars.remove(tvar)
                    break
            else:
                assert False

    def silly_infer(self, type: Type, env: KindEnv):
        match type:
            case TypeConstant():
                _assign(type, ATOM_KIND, env)
            case TypeApp(f, args):
                assert isinstance(f, TypeConstant)
                assert all(isinstance(type_arg, TypeVar) for type_arg in args)

                for type_arg in args:
                    type_arg._kind = ATOM_KIND

                _assign(f, FunctionKind([ATOM_KIND for _ in args] + [ATOM_KIND]), env)
            case _:
                assert False
