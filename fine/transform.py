"""Transformer:

- tranforms 'OpChain' ASTs in 'BinaryOperation' ASTs
"""

from . import ast, visitor
from .ast.base import Expr
from .utils import Scope, String


type SigScope = Scope[str, ast.FixitySignature]


IS_LEFT_ASSOC = True
PRECEDENCE = 10


class Transformer:
    def _create_binop(self, infixn: list[Expr | String], scope: SigScope):
        rpn: list[Expr | String] = []
        op_stack: list[String] = []
        for item in infixn:
            if isinstance(item, ast.Expr):
                rpn.append(item)
                continue

            curr = scope.get(item)
            curr_prec = curr.precedence if curr else PRECEDENCE
            is_curr_lassoc = curr.is_left_associative if curr else IS_LEFT_ASSOC

            while len(op_stack) > 0:
                top = scope.get(op_stack[-1])
                top_prec = top.precedence if top else PRECEDENCE

                if top_prec > curr_prec or top_prec == curr_prec and is_curr_lassoc:
                    rpn.append(op_stack.pop())
                else:
                    break

            op_stack.append(item)

        while len(op_stack) > 0:
            rpn.append(op_stack.pop())

        operands: list[Expr] = []
        for item in rpn:
            if isinstance(item, Expr):
                operands.append(item)
                continue

            right = operands.pop()
            left = operands.pop()
            operands.append(ast.BinaryOperation(left, item, right))

        assert len(operands) == 1
        return operands[0]

    @visitor.on("node")
    def visit(self, node, scope):
        pass

    @visitor.when(ast.Type)
    def visit(self, node: ast.Type, scope):
        return node

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
        return node

    @visitor.when(ast.FunctionApp)
    def visit(self, node: ast.FunctionApp, scope):
        node.target = self.visit(node.target, scope)
        node.arg = self.visit(node.arg, scope)

        return node

    @visitor.when(ast.OpChain)
    def visit(self, node: ast.OpChain, scope: SigScope):
        elements = [
            self.visit(el, scope) if isinstance(el, Expr) else el
            for el in node.elements
        ]

        return self._create_binop(elements, scope)

    @visitor.when(ast.Function)
    def visit(self, node: ast.Function, scope):
        node.body = self.visit(node.body, scope)

        return node

    @visitor.when(ast.LetExpr)
    def visit(self, node: ast.LetExpr, scope: SigScope):
        scope = scope.new_scope()

        for defn in node.definitions:
            self.visit(defn, scope)
        node.body = self.visit(node.body, scope)

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

    @visitor.when(ast.ValueDefn)
    def visit(self, node: ast.ValueDefn, scope: SigScope):
        node.value = self.visit(node.value, scope)

        return node

    @visitor.when(ast.ValueTypeDefn)
    def visit(self, node: ast.ValueTypeDefn, scope):
        return node

    @visitor.when(ast.FixitySignature)
    def visit(self, node: ast.FixitySignature, scope: SigScope):
        scope.add(node.operator, node)

        return node

    @visitor.when(ast.Module)
    def visit(self, node: ast.Module, scope):
        for defn in node.definitions:
            self.visit(defn, scope)

        return node
