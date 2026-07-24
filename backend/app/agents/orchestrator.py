import structlog
from typing import Dict, Any
from app.agents.intent_detector import IntentDetector
from app.agents.planner import Planner
from app.agents.execution_context import ExecutionContext
from app.tools.registry import ToolRegistry
from app.tools.tool_executor import ToolExecutor

logger = structlog.get_logger("aegis.agents")

class Orchestrator:
    """Orchestrates intent classification, planning, safety gates, and deterministic tool execution."""
    
    @staticmethod
    def execute_orchestration(question: str, context: ExecutionContext) -> Dict[str, Any]:
        """Coordinates pipeline processing and returns execution metrics and outputs."""
        # 1. Intent detection
        intent_info = IntentDetector.detect_intent(question)
        
        # 2. Planning
        plan = Planner.generate_plan(question, intent_info)
        tool_name = plan.get("tool_name")
        
        if not tool_name:
            return {
                "intent": intent_info["intent"],
                "tool_execution": None
            }
            
        # Dynamically register built-in tools if registry is empty
        ToolRegistry.register_builtin_tools()
        tool = ToolRegistry.get_tool(tool_name)
        
        if not tool:
            logger.warn("requested_tool_not_registered", tool=tool_name)
            return {
                "intent": intent_info["intent"],
                "tool_execution": None
            }
            
        # 3. Safety Guard validation + 4. Execution
        params = plan["parameters"].copy()
        params["workspace_id"] = context.workspace_id
        
        exec_res = ToolExecutor.execute_tool(
            tool=tool,
            params=params,
            user_permissions=context.permissions
        )
        
        return {
            "intent": intent_info["intent"],
            "tool_execution": exec_res
        }
