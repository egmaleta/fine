from ..utils import String
from . import Type, TypeConstant, TypeVar, TypeApp, FunctionType, TypeScheme


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


def _quantify(type: Type) -> set[String]:
    match type:
        case TypeConstant():
            return set()

        case TypeVar(name):
            return {name}

        case TypeApp(f, args):
            vars = _quantify(f)
            for targ in args:
                vars |= _quantify(targ)
            return vars

        case FunctionType(args):
            vars = set()
            for targ in args:
                vars |= _quantify(targ)
            return vars

        case TypeScheme(vars, inner):
            captured = _quantify(inner)
            _assert_unused(vars - captured)

            free = captured - vars
            return free


def quantify(type: Type):
    free = _quantify(type)

    match type:
        case TypeScheme():
            _assert_free(free)
            return type
        case _:
            return TypeScheme(free, type) if len(free) > 0 else type
