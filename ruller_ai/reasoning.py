"""Constrained arithmetic evaluator. Never uses eval() or exec()."""
import ast
import math
import operator
from typing import Union

Number = Union[int, float]
_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class UnsafeExpression(ValueError):
    """Raised when an arithmetic expression is outside the allowlist."""


def safe_calculate(expression: str) -> Number:
    expression = expression.strip()
    if not expression or len(expression) > 200:
        raise UnsafeExpression("Enter a non-empty arithmetic expression up to 200 characters.")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError) as exc:
        raise UnsafeExpression("That is not a valid arithmetic expression.") from exc
    if sum(1 for _ in ast.walk(tree)) > 64:
        raise UnsafeExpression("Expression is too complex.")

    def visit(node: ast.AST) -> Number:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1_000_000_000:
                raise UnsafeExpression("Number is too large.")
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and (abs(right) > 10 or abs(left) > 1_000_000):
                raise UnsafeExpression("Exponentiation is limited for safety.")
            try:
                result = _BINARY[type(node.op)](left, right)
            except (ArithmeticError, OverflowError, ValueError) as exc:
                raise UnsafeExpression(f"Calculation failed: {exc}") from exc
            if not isinstance(result, (int, float)) or not math.isfinite(result):
                raise UnsafeExpression("Result is not a finite number.")
            if abs(result) > 1e100:
                raise UnsafeExpression("Result is too large.")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](visit(node.operand))
        raise UnsafeExpression("Only numbers and +, -, *, /, //, %, **, and parentheses are allowed.")

    return visit(tree)
