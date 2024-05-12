from .. import visitor
from . import type as t


class Quantifier:
    def __init__(self):
        self.errors = []

    @visitor.on("type")
    def _visit(self, type):
        pass

    @visitor.when(t.TypeConstant)
    def _visit(self, type):
        return set()

    @visitor.when(t.TypeVar)
    def _visit(self, type: t.TypeVar):
        return {type.name}

    @visitor.when(t.TypeApp)
    def _visit(self, type: t.TypeApp):
        names = {}
        for arg in type.args:
            names |= self._visit(arg)

        return names

    @visitor.when(t.QuantifiedType)
    def _visit(self, type: t.QuantifiedType):
        names = self._visit(type.type)

        captured = type.quantified & names
        free = type.quantified - names
        unused = type.quantified - captured

        for name in unused:
            self.errors.append(f"quantified type var '{name}' is unused")

        return free

    def quantify(self, type: t.Type):
        if not isinstance(type, t.QuantifiedType):
            names = self._visit(type)
            return (
                t.QuantifiedType(names, type) if len(names) > 0 else type
            ), self.errors

        free = self._visit(type)
        for name in free:
            self.errors.append(f"type var '{name}' is not quantified")

        return type, self.errors
