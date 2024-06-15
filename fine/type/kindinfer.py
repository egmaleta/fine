from dataclasses import dataclass

from .type import *

from ..utils import String

@dataclass
class _Equation:
    left: TypeConstant | TypeVar
    right: list[Type]
    env: KindEnv

    def __post_init__(self):
        _, found = self.env.get(self.left.name)
        assert found

    def solved(self):
        try:
            kind = kindof(self.left, self.env)
        except AssertionError:
            pass
        else:
            # solve right
            for type in self.right:
                if isinstance(type, (TypeConstant, TypeVar)):
                    tkind, found = self.env.get(type.name)
                    if found and tkind is None:
                        self.env.set(type.name, kind.left)
                kind = kind.right

            return True

        # solve left
        try:
            kind = FunctionKind([kindof(type, self.env) for type in self.right] + [ATOM_KIND])
        except AssertionError:
            pass
        else:
            self.env.set(self.left.name, kind)
            return True

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
                    kinds = [self._infer(type_arg, env) for type_arg in args]
                    if None not in kinds:
                        self._assign(f, FunctionKind([*kinds, ATOM_KIND]), env)
                    else:
                        eq = _Equation(f, args, env)
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
                            eq.env.set(name, ATOM_KIND)
                    self._tvar_names.remove(name)
                    break
            else:
                assert False, self._equations

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