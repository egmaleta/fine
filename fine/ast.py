from dataclasses import dataclass, field

from .pattern import Pattern
from .type import Type, TypeConstant, TypeApp
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
    args: list[Expr]


@dataclass
class OpChain(Expr):
    """Expected to be transformed in a tree of `FunctionApp`."""

    chain: list[String | Expr]


@dataclass
class LetExpr(Expr):
    defns: list[Defn]
    body: Expr


@dataclass
class PatternMatching(Expr):
    matchable: Expr
    matches: list[tuple[Pattern, Expr]]


@dataclass
class Guards(Expr):
    conditionals: list[tuple[Expr, Expr]]
    fallback: Expr


@dataclass
class Function(Expr):
    params: list[String]
    body: Expr


@dataclass
class ValueDefn(Defn):
    name: String
    value: Expr


@dataclass
class TypeDefn(Defn):
    name: String
    type: Type


@dataclass
class DatatypeDefn(Defn):
    type: TypeConstant | TypeApp
    val_defns: list[ValueDefn] = field(default_factory=lambda: [])
    type_defns: list[TypeDefn] = field(default_factory=lambda: [])

    def __post_init__(self):
        assert len(self.val_defns) == len(self.type_defns)
        for val_defn, type_defn in zip(self.val_defns, self.type_defns):
            assert val_defn.name == type_defn.name


@dataclass
class FixitySignature(Defn):
    operators: list[String]
    is_left_associative: bool
    precedence: int


@dataclass
class Module(Defn):
    defns: list[Defn]
