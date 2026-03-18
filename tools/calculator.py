"""
Safe math expression evaluator.
Supports basic arithmetic, power, modulo, and common math functions.
"""

import math
import ast
import operator

# Allowed operators and functions for safe evaluation
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    "min": min,
    "max": max,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
}


def _safe_eval(node):
    """Recursively evaluate an AST node with only safe operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value}")
    elif isinstance(node, ast.BinOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op(_safe_eval(node.operand))
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func = _SAFE_FUNCTIONS.get(node.func.id)
            if func is None:
                raise ValueError(f"Unsupported function: {node.func.id}")
            args = [_safe_eval(arg) for arg in node.args]
            return func(*args)
        raise ValueError("Unsupported call expression")
    elif isinstance(node, ast.Name):
        val = _SAFE_FUNCTIONS.get(node.id)
        if val is None:
            raise ValueError(f"Unsupported name: {node.id}")
        return val
    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.
    Returns the numeric result as a string.
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression '{expression}': {e}"
