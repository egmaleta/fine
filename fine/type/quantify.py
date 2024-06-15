from ..utils import String

from . import type as t


def _format_vars(vars):
    match [*vars]:
        case [var]:
            return f"Type variable '{var}' is"
        case [*leading, last]:
            leading = ", ".join(f"'{v}'" for v in leading)
            return f"Type variables {leading} and '{last}' are"


def _assert_unused(vars: set[String]):
    assert len(vars) == 0, f"{_format_vars(vars)} unused."


def _assert_free(vars: set[String]):
    assert len(vars) == 0, f"{_format_vars(vars)} free."


def _quantify(type: t.Type) -> set[String]:
    match type:
        case t.TypeConstant():
            return set()

        case t.TypeVar(name):
            return {name}

        case t.TypeApp(f, args):
            vars = _quantify(f)
            for type in args:
                vars |= _quantify(type)
            return vars

        case t.FunctionType(args):
            vars = set()
            for type in args:
                vars |= _quantify(type)
            return vars

        case t.TypeScheme(vars, inner):
            captured = _quantify(inner)
            _assert_unused(vars - captured)

            free = captured - vars
            return free


def quantify(type: t.Type):
    free = _quantify(type)

    match type:
        case t.TypeScheme():
            _assert_free(vars)
            return type
        case _:
            return t.TypeScheme(free, type) if len(free) > 0 else type
