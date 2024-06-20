from dataclasses import dataclass

from . import ast
from .type import Type
from .utils import Env


@dataclass
class _Equation:
    left: Type
    right: Type


class TypeInferer:
    def _infer(self, expr: ast.Expr, env: Env[Type | None]):
        match expr:
            case ast.InternalValue():
                pass

            case ast.InternalFunction():
                pass

            case ast.Data():
                pass

            case ast.PolyData():
                pass

            case ast.Int():
                pass

            case ast.Float():
                pass

            case ast.Unit():
                pass

            case ast.Str():
                pass

            case ast.Id():
                pass

            case ast.FunctionApp():
                pass

            case ast.Guards():
                pass

            case ast.Function():
                pass

            case ast.PatternMatching():
                pass

            case ast.LetExpr():
                pass

            case _:
                assert False

    def infer(self, exprs: list[ast.Expr], env: Env[Type | None]):
        pass
