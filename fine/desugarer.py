# Most of desugaring happens at grammar attributes.
# Desugaring dependant of any context happens here.
#
# For example, desugaring a chain of operations requires
# to know the precedence and associativity of an operator
# at a given scope.

from lark.lexer import Token

from .scope import Scope
from . import ast
from . import visitor


type FixitySignature = ast.ValueDefn.FixitySignature


class Desugarer:
    def _build_operation(
        self, infixn: list[ast.Expr | Token], scope: Scope[FixitySignature]
    ):
        rpn: list[ast.Expr | Token] = []
        op_stack: list[Token] = []
        for item in infixn:
            if isinstance(item, ast.Expr):
                rpn.append(item)
                continue

            curr = scope.get_item(item.value)
            assert curr is not None

            while len(op_stack) > 0:
                top = scope.get_item(op_stack[-1].value)
                assert top is not None

                if (
                    top.precedence > curr.precedence
                    or top.precedence == curr.precedence
                    and curr.is_left_associative
                ):
                    rpn.append(op_stack.pop())
                else:
                    break

            op_stack.append(item)

        while len(op_stack) > 0:
            rpn.append(op_stack.pop())

        operands: list[ast.Expr] = []
        for item in rpn:
            if isinstance(item, ast.Expr):
                operands.append(item)
                continue

            right = operands.pop()
            left = operands.pop()
            operands.append(ast.Operation(left, item, right))

        assert len(operands) == 1
        return operands[0]

    @visitor.on("node")
    def visit(self, node, scope):
        pass

    @visitor.when(ast.ExternalExpr)
    def visit(self, node: ast.ExternalExpr, scope: Scope[FixitySignature]):
        return node

    @visitor.when(ast.Data)
    def visit(self, node: ast.Data, scope: Scope[FixitySignature]):
        return node

    @visitor.when(ast.Identifier)
    def visit(self, node: ast.Identifier, scope: Scope[FixitySignature]):
        return node

    @visitor.when(ast.FunctionApp)
    def visit(self, node: ast.FunctionApp, scope: Scope[FixitySignature]):
        node.target = self.visit(node.target, scope)
        node.arg = self.visit(node.arg, scope)
        return node

    @visitor.when(ast.OpChain)
    def visit(self, node: ast.OpChain, scope: Scope[FixitySignature]):
        elements = [
            self.visit(el, scope) if isinstance(el, ast.Expr) else el
            for el in node.elements
        ]
        return self._build_operation(elements, scope)

    @visitor.when(ast.Function)
    def visit(self, node: ast.Function, scope: Scope[FixitySignature]):
        node.body = self.visit(node.body, scope)
        return node

    @visitor.when(ast.Block)
    def visit(self, node: ast.Block, scope: Scope[FixitySignature]):
        node.actions = [self.visit(action, scope) for action in node.actions]
        node.body = self.visit(node.body, scope)
        return node

    @visitor.when(ast.LetExpr)
    def visit(self, node: ast.LetExpr, scope: Scope[FixitySignature]):
        child_scope = scope.new_child()
        self.visit(node.definition, child_scope)
        node.body = self.visit(node.body, child_scope)
        return node

    @visitor.when(ast.PatternMatching)
    def visit(self, node: ast.PatternMatching, scope: Scope[FixitySignature]):
        node.matchable = self.visit(node.matchable, scope)
        node.matches = [
            (pattern, self.visit(body, scope)) for pattern, body in node.matches
        ]
        return node

    @visitor.when(ast.Conditional)
    def visit(self, node: ast.Conditional, scope: Scope[FixitySignature]):
        node.condition = self.visit(node.condition, scope)
        node.body = self.visit(node.body, scope)
        node.fall_body = self.visit(node.fall_body, scope)
        return node

    @visitor.when(ast.ValueDefn)
    def visit(self, node: ast.ValueDefn, scope: Scope[FixitySignature]):
        if node.fixity_sig is not None:
            assert node.fixity_sig.precedence <= 10
            scope.add_item(node.name, node.fixity_sig)
        else:
            sig = ast.ValueDefn.FixitySignature(True, 9)
            scope.add_item(node.name, sig)

        node.value = self.visit(node.value, scope)
        return node

    @visitor.when(ast.Module)
    def visit(self, node: ast.Module, scope: Scope[FixitySignature]):
        for defn in node.definitions:
            self.visit(defn, scope)
            scope = scope.new_child()
        return node
