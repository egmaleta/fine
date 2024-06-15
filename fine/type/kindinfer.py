from dataclasses import dataclass

from .type import *

from ..utils import String


@dataclass
class _Equation:
    left: TypeConstant | TypeVar
    right: list[Kind | TypeConstant | TypeVar]
    env: KindEnv

    def __post_init__(self):
        _, found = self.env.get(self.left.name)
        assert found

    def _kindof(self, type: TypeConstant | TypeVar):
        kind, found = self.env.get(type.name)
        assert found
        return kind

    def solved(self):
        lkind = self._kindof(self.left)
        if lkind is not None:
            for item in self.right:
                assert isinstance(lkind, FunctionKind)

                if not isinstance(item, Kind) and self._kindof(item) is None:
                    assert self.env.set(item.name, lkind.left)

                lkind = lkind.right

            return True

        new_right = []
        all_solved = True
        for item in self.right:
            if isinstance(item, Kind):
                new_right.append(item)
                continue

            kind = self._kindof(item)
            if kind is not None:
                new_right.append(kind)
                continue

            all_solved = False
            new_right.append(item)

        if all_solved:
            rkind = FunctionKind([*new_right, ATOM_KIND])
            assert self.env.set(self.left.name, rkind)

            return True

        self.right = new_right
        return False


class KindInferer:
    def __init__(self):
        self._equations: list[_Equation] = []
        self._tvar_names: list[String] = []

    def _assign(self, type: Type, kind: Kind, env: KindEnv):
        assert isinstance(type, (TypeConstant, TypeVar))
        assert env.set(type.name, kind)

    def _infer(self, type: Type, env: KindEnv):
        match type:
            case TypeConstant(name):
                kind, found = env.get(name)
                assert found
                return kind

            case TypeVar(name):
                self._tvar_names.append(name)

                kind, found = env.get(name)
                assert found
                return kind

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
                        self._assign(f, FunctionKind([*items, ATOM_KIND]), env)
                    else:
                        eq = _Equation(f, items, env)
                        self._equations.append(eq)

                else:
                    for type_arg in args:
                        assert isinstance(fkind, FunctionKind)
                        lkind = fkind.left

                        kind = self._infer(type_arg, env)
                        if kind is None:
                            self._assign(type_arg, lkind, env)

                        fkind = fkind.right

                return ATOM_KIND

            case FunctionType() as ftype:
                # kind(->) == * -> *
                for type_arg in [ftype.left, ftype.right]:
                    kind = self._infer(type_arg, env)
                    if kind is None:
                        self._assign(type_arg, ATOM_KIND, env)

                return ATOM_KIND

            case TypeScheme(vars, inner):
                env = env.child_env()
                for name in vars:
                    env.add(name, None)

                if type._env is None:
                    type._env = env

                kind = self._infer(inner, env)
                if kind is None:
                    self._assign(inner, ATOM_KIND, env)

                return ATOM_KIND

    def infer(self, types: list[Type], env: KindEnv):
        for type in types:
            kind = self._infer(type, env)
            if kind is None:
                self._assign(type, ATOM_KIND, env)

        leftside_names = [eq.left.name for eq in self._equations]
        while True:
            prev_len = len(self._equations)

            self._equations = [eq for eq in self._equations if not eq.solved()]
            new_len = len(self._equations)

            if new_len == 0:
                return

            if new_len < prev_len:
                continue

            for name in self._tvar_names:
                if name not in leftside_names:
                    for eq in self._equations:
                        kind, found = eq.env.get(name)
                        if found and kind is None:
                            assert eq.env.set(name, ATOM_KIND)
                    self._tvar_names.remove(name)
                    break
            else:
                assert False

    def silly_infer(self, type: Type, env: KindEnv):
        match type:
            case TypeConstant(name):
                env.set(name, ATOM_KIND)
            case TypeApp(f, args):
                assert isinstance(f, TypeConstant)
                assert all(isinstance(type_arg, TypeVar) for type_arg in args)

                env.set(f.name, FunctionKind([ATOM_KIND for _ in args] + [ATOM_KIND]))
            case _:
                assert False
