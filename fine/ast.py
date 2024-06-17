from dataclasses import dataclass, field
from typing import Union

from .pattern import Pattern
from .type import Type, TypeConstant, TypeVar, TypeApp
from .utils import String


class AST:
    pass


class Defn(AST):
    pass


class Expr(AST):
    pass


@dataclass
class InternalValue(Expr):
    """A value provided by the compiler.

    `name` is the identifier of the value."""

    name: String


@dataclass
class InternalFunction(Expr):
    """A function provided by the compiler.

    `name` is the identifier of the function.

    `arg_names` are the names of the values in scope expected to be passed to the function.
    """

    name: String
    arg_names: list[String]


@dataclass
class Data(Expr):
    """Data created by constant data constructors.

    `tag` is the name of the constructor and the actual data."""

    tag: String


@dataclass
class PolyData(Expr):
    """Data created by function data constructors.

    `tag` is the name of the constructor.

    `value_names` are the names of the values in scope used to create the piece of data.
    """

    tag: String
    value_names: list[String]


@dataclass
class Int(Expr):
    value: String


@dataclass
class Float(Expr):
    value: String


@dataclass
class Unit(Expr):
    value: String


@dataclass
class Str(Expr):
    value: String


@dataclass
class Id(Expr):
    name: String


@dataclass
class FunctionApp(Expr):
    f: Expr
    arg: Expr


@dataclass
class OpChain(Expr):
    """Expected to be transformed in a tree of `FunctionApp`."""

    chain: list[String | Expr]


@dataclass
class Guards(Expr):
    conditionals: list[tuple[Expr, Expr]]
    fallback: Expr


@dataclass
class Function(Expr):
    params: list[tuple[String, bool]]
    body: Expr


@dataclass
class PatternMatching(Expr):
    matchable: Expr
    matches: list[tuple[Pattern, Expr]]


@dataclass
class LetExpr(Expr):
    defns: list[Union["Binding", "Typing", "FixitySignature"]]
    body: Expr


@dataclass
class Binding(Defn):
    name: String
    value: Expr


@dataclass
class Typing(Defn):
    name: String
    type: Type


@dataclass
class DatatypeDefn(Defn):
    type: TypeConstant | TypeApp
    bindings: list[Binding] = field(default_factory=lambda: [])
    typings: list[Typing] = field(default_factory=lambda: [])

    def __post_init__(self):
        match self.type:
            case TypeApp(f, args):
                assert isinstance(f, TypeConstant)
                assert all(isinstance(type_arg, TypeVar) for type_arg in args)

        assert len(self.bindings) == len(self.typings)
        for binding, typing in zip(self.bindings, self.typings):
            assert binding.name == typing.name

    @property
    def is_internal(self):
        return len(self.typings) == 0


@dataclass
class FixitySignature(Defn):
    operators: list[String]
    is_left_associative: bool
    precedence: int


@dataclass
class Module(Defn):
    defns: list[Defn]
