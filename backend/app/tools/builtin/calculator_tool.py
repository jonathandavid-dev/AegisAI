import ast
import operator
from typing import Dict, Any
from app.tools.base_tool import BaseTool

class CalculatorTool(BaseTool):
    """Safe evaluation calculator using Abstract Syntax Tree parsing."""
    
    @property
    def name(self) -> str:
        return "calculator"
        
    @property
    def description(self) -> str:
        return (
            "Safely evaluates basic arithmetic expressions. "
            "Supported operations: addition (+), subtraction (-), multiplication (*), "
            "division (/), exponentiation (**), modulo (%), positive (+x), negative (-x)."
        )
        
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "expression": {
                "type": "string",
                "description": "Math expression string, e.g. '14500 * 0.18'",
                "required": True
            }
        }
        
    def validate(self, params: Dict[str, Any]) -> bool:
        if "expression" not in params or not isinstance(params["expression"], str):
            return False
        return len(params["expression"].strip()) > 0
        
    def execute(self, params: Dict[str, Any]) -> Any:
        expr = params["expression"]
        try:
            allowed_operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos
            }
            
            def _eval(node):
                if isinstance(node, ast.Constant):
                    if isinstance(node.value, (int, float)):
                        return node.value
                    raise ValueError("Constants must be numeric.")
                elif isinstance(node, ast.BinOp):
                    op_type = type(node.op)
                    if op_type not in allowed_operators:
                        raise TypeError(f"Operation {op_type.__name__} is not supported.")
                    return allowed_operators[op_type](_eval(node.left), _eval(node.right))
                elif isinstance(node, ast.UnaryOp):
                    op_type = type(node.op)
                    if op_type not in allowed_operators:
                        raise TypeError(f"Unary operation {op_type.__name__} is not supported.")
                    return allowed_operators[op_type](_eval(node.operand))
                else:
                    raise TypeError(f"Expressions with node type {type(node).__name__} are blocked.")
                    
            parsed = ast.parse(expr, mode='eval')
            result = _eval(parsed.body)
            return {"expression": expr, "result": result}
        except Exception as exc:
            raise ValueError(f"Failed to evaluate expression securely: {str(exc)}")
