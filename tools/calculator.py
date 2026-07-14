"""
calculator.py

Safe mathematical calculator tool for Gemini Function Calling.
"""

import ast
import operator


# Supported Operators
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _evaluate(node):
    """
    Recursively evaluates an AST expression.
    """

    if isinstance(node, ast.Constant):
        return node.value

    elif isinstance(node, ast.BinOp):

        left = _evaluate(node.left)
        right = _evaluate(node.right)

        return OPERATORS[type(node.op)](left, right)

    elif isinstance(node, ast.UnaryOp):

        operand = _evaluate(node.operand)

        return OPERATORS[type(node.op)](operand)

    else:
        raise TypeError("Unsupported mathematical expression.")


def calculator(expression: str) -> str:
    """
    Safely evaluates a mathematical expression.

    Example:
        calculator("25 * (10 + 5)")
    """

    print("\n[Calculator Tool Called]")

    try:

        parsed = ast.parse(
            expression,
            mode="eval"
        )

        result = _evaluate(parsed.body)

        return (
            f"Calculation Result\n"
            f"Expression : {expression}\n"
            f"Result     : {result}"
        )

    except Exception as e:

        return f"Calculator Error: {e}"