from .base import String, Expr
from .ast import Function
from .type import Type, FunctionType


def typelist_of_ftype(ft: FunctionType):
    types = []

    while isinstance(ft, FunctionType):
        types.append(ft.left)
        ft = ft.right

    types.append(ft)
    return types


def create_function(params: list[String], body: Expr):
    assert len(params) >= 1

    f = body
    for p in reversed(params):
        f = Function(p, f)

    return f


def create_typed_function(params: list[String], param_types: list[Type], body: Expr):
    l = len(params)
    assert l >= 1 and l == len(param_types)

    f = body
    for p, t in zip(reversed(params), reversed(param_types)):
        f = Function(p, f, t)

    return f
