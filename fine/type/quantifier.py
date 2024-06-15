from .type import *

from ..utils import String


class Quantifier:
    @staticmethod
    def _format_vars(vars):
        match [*vars]:
            case [var]:
                return f"Type variable '{var}' is"
            case [*leading, last]:
                leading = ", ".join(f"'{v}'" for v in leading)
                return f"Type variables {leading} and '{last}' are"

    @staticmethod
    def _assert_unused(vars: set[String]):
        assert len(vars) == 0, f"{Quantifier._format_vars(vars)} unused."

    @staticmethod
    def _assert_free(vars: set[String]):
        assert len(vars) == 0, f"{Quantifier._format_vars(vars)} free."

    def _quantify(self, type: Type):
        match type:
            case TypeConstant():
                return set()

            case TypeVar(name):
                return {name}

            case TypeApp(f, args):
                vars = self._quantify(f)
                for type in args:
                    vars |= self._quantify(type)
                return vars

            case FunctionType(args):
                vars = set()
                for type in args:
                    vars |= self._quantify(type)
                return vars

            case TypeScheme(vars, inner):
                captured = self._quantify(inner)

                self._assert_unused(vars - captured)

                free = captured - vars
                return free

    def quantify(self, type: Type):
        free = self._quantify(type)

        if not isinstance(type, TypeScheme):
            return TypeScheme(free, type) if len(free) > 0 else type

        self._assert_free(free)

        return type
