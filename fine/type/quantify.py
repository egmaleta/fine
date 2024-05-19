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
                names = {f.name}
                for arg in args:
                    names |= self._quantify(arg)

                return names

            case t.QuantifiedType(quantified, inner):
                names = self._quantify(inner)

                captured = quantified & names
                free = quantified - names
                unused = quantified - captured

                for name in unused:
                    self.errors.append(f"quantified type var '{name}' is unused")

                return free

    def quantify(self, type: t.Type):
        if not isinstance(type, t.QuantifiedType):
            names = self._quantify(type)
            return (
                t.QuantifiedType(names, type) if len(names) > 0 else type
            ), self.errors

        free = self._quantify(type)
        for name in free:
            self.errors.append(f"type var '{name}' is not quantified")

        return type, self.errors
