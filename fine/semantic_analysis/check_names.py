"""NameChecker:

- checks the existence of types

- checks the existence of value, function and constructor names

- checks the existence of a 'ValueDefn' for every 'ValueTypeDefn' (in the same scope)

- checks the existence of an operator for every 'FixitySignature'

- searches for duplicate 'ValueDefn' names (in the same scope)

- searches for duplicate 'Type' and constructor names (in the same scope)

- searches for duplicate 'FixitySignature' operators (in the same scope)
"""

from .. import ast, visitor
from ..utils import Scope


type NameScope = Scope[str, bool]


class NameChecker:
    @visitor.on("node")
    def visit(self, node, scope):
        pass

    @visitor.when(ast.InternalValue)
    def visit(self, node, scope):
        return node

    @visitor.when(ast.NullaryData)
    def visit(self, node, scope):
        return node

    @visitor.when(ast.Data)
    def visit(self, node, scope):
        return node

    @visitor.when(ast.Id)
    def visit(self, node, scope):
        pass  # TODO

    @visitor.when(ast.FunctionApp)
    def visit(self, node: ast.FunctionApp, scope):
        self.visit(node.target, scope)
        self.visit(node.arg, scope)

        return node

    @visitor.when(ast.OpChain)
    def visit(self, node: ast.OpChain, scope):
        for el in node.elements:
            self.visit(el, scope)

        return node

    @visitor.when(ast.BinaryOperation)
    def visit(self, node: ast.BinaryOperation, scope):
        pass  # TODO

    @visitor.when(ast.Function)
    def visit(self, node: ast.Function, scope):
        pass  # TODO

    @visitor.when(ast.LetExpr)
    def visit(self, node: ast.LetExpr, scope: NameScope):
        scope = scope.new_scope()

        for defn in node.definitions:
            self.visit(defn, scope)
        self.visit(node.body, scope)

        return node

    @visitor.when(ast.PatternMatching)
    def visit(self, node: ast.PatternMatching, scope):
        node.matchable = self.visit(node.matchable, scope)
        node.matches = [(p, self.visit(expr, scope)) for p, expr in node.matches]

        return node

    @visitor.when(ast.Conditional)
    def visit(self, node: ast.Conditional, scope):
        node.condition = self.visit(node.condition, scope)
        node.body = self.visit(node.body, scope)
        node.fall_body = self.visit(node.fall_body, scope)

        return node

    @visitor.when(ast.Constructor)
    def visit(self, node: ast.Constructor, scope):
        return node

    @visitor.when(ast.ValueDefn)
    def visit(self, node: ast.ValueDefn, scope: NameScope):
        node.value = self.visit(node.value, scope)

        return node

    @visitor.when(ast.FixitySignature)
    def visit(self, node: ast.FixitySignature, scope: NameScope):
        scope.add(node.operator, node)

        return node

    @visitor.when(ast.ValueTypeDefn)
    def visit(self, node: ast.ValueTypeDefn, scope):
        return node

    @visitor.when(ast.Type)
    def visit(self, node: ast.Type, scope):
        return node

    @visitor.when(ast.Module)
    def visit(self, node: ast.Module, scope):
        for defn in node.definitions:
            self.visit(defn, scope)

        return node
