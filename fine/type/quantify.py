from . import type as t


class Quantifier:
    def __init__(self):
        self.errors: list[str] = []

    def _quantify(self, type: t.Type) -> set[str]:
        match type:
            case t.TypeConstant():
                return set()

            case t.TypeVar(name):
                return {name}

            case t.TypeApp(f, args):
                vars = self._quantify(f)
                for type in args:
                    vars |= self._quantify(type)
                return vars

            case t.FunctionType(args):
                vars = {}
                for type in args:
                    vars |= self._quantify(type)
                return vars

            case t.ConstrainedType(_, inner):
                return self._quantify(inner)

            case t.TypeScheme(vars, inner):
                captured = self._quantify(inner)

                free = captured - vars
                unused = vars - captured

                for name in unused:
                    self.errors.append(f"quantified type var '{name}' is unused")

                return free

    def quantify(self, type: t.Type):
        if not isinstance(type, t.TypeScheme):
            vars = self._quantify(type)
            return (t.TypeScheme(vars, type) if len(vars) > 0 else type), self.errors

        free = self._quantify(type)
        for name in free:
            self.errors.append(f"type var '{name}' is not quantified")

        return type, self.errors
