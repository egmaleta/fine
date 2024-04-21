# Most of desugaring happens at grammar attributes.
# Desugaring dependant of any context happens here.
#
# For example, desugaring a chain of operations requires
# to know the precedence and associativity of an operator
# at a given scope.

from vendor import visitor

from .scope import Scope
from .lexer import Token
from . import ast


class Desugarer:
    def _build_operation(
        self, infixn: list[ast.Expr | Token], scope: Scope[ast.OperationInfo]
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
                    and curr.is_left_assoc
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

    @visitor.when(ast.InternalExpr)
    def visit(self, node: ast.InternalExpr, scope: Scope[ast.OperationInfo]):
        return node

    @visitor.when(ast.Data)
    def visit(self, node: ast.Data, scope: Scope[ast.OperationInfo]):
        return node

    @visitor.when(ast.Identifier)
    def visit(self, node: ast.Identifier, scope: Scope[ast.OperationInfo]):
        return node

    @visitor.when(ast.FunctionApp)
    def visit(self, node: ast.FunctionApp, scope: Scope[ast.OperationInfo]):
        node.target = self.visit(node.target, scope)
        node.arg = self.visit(node.arg, scope)
        return node

    @visitor.when(ast.OpChain)
    def visit(self, node: ast.OpChain, scope: Scope[ast.OperationInfo]):
        elements = [
            self.visit(el, scope) if isinstance(el, ast.Expr) else el
            for el in node.elements
        ]
        return self._build_operation(elements, scope)

    @visitor.when(ast.Function)
    def visit(self, node: ast.Function, scope: Scope[ast.OperationInfo]):
        node.body = self.visit(node.body, scope)
        return node

    @visitor.when(ast.Block)
    def visit(self, node: ast.Block, scope: Scope[ast.OperationInfo]):
        node.actions = [self.visit(action, scope) for action in node.actions]
        node.body = self.visit(node.body, scope)
        return node

    @visitor.when(ast.LetExpr)
    def visit(self, node: ast.LetExpr, scope: Scope[ast.OperationInfo]):
        child_scope = scope.new_child()
        for defn in node.definitions:
            self.visit(defn, child_scope)
        node.body = self.visit(node.body, child_scope)
        return node

    @visitor.when(ast.PatternMatching)
    def visit(self, node: ast.PatternMatching, scope: Scope[ast.OperationInfo]):
        node.matchable = self.visit(node.matchable, scope)
        node.matches = [
            (pattern, self.visit(body, scope)) for pattern, body in node.matches
        ]
        return node

    @visitor.when(ast.ValueDefn)
    def visit(self, node: ast.ValueDefn, scope: Scope[ast.OperationInfo]):
        node.value = self.visit(node.value, scope)
        return node

    @visitor.when(ast.OperationInfo)
    def visit(self, node: ast.OperationInfo, scope: Scope[ast.OperationInfo]):
        scope.add_item(node.operator, node)
        return node

    @visitor.when(ast.Program)
    def visit(self, node: ast.Program, scope: Scope[ast.OperationInfo]):
        for defn in node.definitions:
            self.visit(defn, scope)
        return node
