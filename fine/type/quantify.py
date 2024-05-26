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

            case t.TypeApp(fname, args):
                vars = {fname}
                for arg in args:
                    vars |= self._quantify(arg)

                return vars

            case t.FunctionType(inner_types):
                vars = {}
                for type in inner_types:
                    vars |= self._quantify(type)

                return vars

            case t.QuantifiedType(quantified, inner_type):
                vars = self._quantify(inner_type)

                free = vars - quantified
                unused = quantified - vars

                for name in unused:
                    self.errors.append(f"quantified type var '{name}' is unused")

                return free

    def quantify(self, type: t.Type):
        if not isinstance(type, t.QuantifiedType):
            vars = self._quantify(type)
            return (
                t.QuantifiedType(vars, type) if len(vars) > 0 else type
            ), self.errors

        free = self._quantify(type)
        for name in free:
            self.errors.append(f"type var '{name}' is not quantified")

        return type, self.errors
