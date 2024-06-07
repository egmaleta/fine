from . import type as t


def _quantify(type: t.Type):
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
            vars = {}
            for type in args:
                vars |= _quantify(type)
            return vars

        case t.ConstrainedType(_, inner):
            return _quantify(inner)

        case t.TypeScheme(vars, inner):
            captured = _quantify(inner)

            unused = vars - captured
            assert len(unused) == 0

            free = captured - vars
            return free


def quantify(type: t.Type):
    free = _quantify(type)

    if not isinstance(type, t.TypeScheme):
        return t.TypeScheme(free, type) if len(free) > 0 else type

    assert len(free) == 0

    return type
