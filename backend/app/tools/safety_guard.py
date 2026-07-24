import structlog
from typing import Dict, Any, List
from app.tools.base_tool import BaseTool

logger = structlog.get_logger("aegis.tools")

class SafetyGuard:
    """Enforces parameter types checks and permission validations on system tool executions."""
    
    @staticmethod
    def validate_execution(tool: BaseTool, params: Dict[str, Any], user_permissions: List[str] = None) -> None:
        """Asserts parameter existence, type schemas, and execution security scopes."""
        if user_permissions is None:
            user_permissions = ["read"]
            
        logger.info("Safety Validation", tool=tool.name)
        
        # 1. Enforce permissions validation
        for permission in tool.permissions:
            if permission not in user_permissions:
                logger.error("safety_permission_rejected", tool=tool.name, required_permission=permission)
                raise PermissionError(f"Access Denied: Tool '{tool.name}' requires permission '{permission}'.")
                
        # 2. Check parameter schemas
        schema = tool.parameters
        for param_name, metadata in schema.items():
            is_required = metadata.get("required", False)
            param_type = metadata.get("type", "string")
            
            if is_required and param_name not in params:
                logger.error("safety_missing_required_param", tool=tool.name, parameter=param_name)
                raise ValueError(f"Validation Error: Tool '{tool.name}' requires parameter '{param_name}'.")
                
            if param_name in params:
                val = params[param_name]
                if param_type == "string" and not isinstance(val, str):
                    raise TypeError(f"Validation Error: Parameter '{param_name}' must be a string.")
                elif param_type == "integer" and not isinstance(val, int):
                    raise TypeError(f"Validation Error: Parameter '{param_name}' must be an integer.")
                elif param_type == "float" and not isinstance(val, (int, float)):
                    raise TypeError(f"Validation Error: Parameter '{param_name}' must be a float.")
                elif param_type == "boolean" and not isinstance(val, bool):
                    raise TypeError(f"Validation Error: Parameter '{param_name}' must be a boolean.")
                    
        # 3. Trigger custom validator checks
        if not tool.validate(params):
            logger.error("safety_tool_custom_validation_failed", tool=tool.name)
            raise ValueError(f"Validation Error: Custom validation checks failed for tool '{tool.name}'.")
