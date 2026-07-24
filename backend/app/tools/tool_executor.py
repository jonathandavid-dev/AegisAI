import time
import structlog
import concurrent.futures
from typing import Dict, Any, List
from app.tools.base_tool import BaseTool
from app.tools.safety_guard import SafetyGuard

logger = structlog.get_logger("aegis.tools")

class ToolExecutor:
    """Executes validated system tools, wrapping errors and timings in response payloads."""
    
    @staticmethod
    def execute_tool(
        tool: BaseTool, 
        params: Dict[str, Any], 
        user_permissions: List[str] = None,
        timeout_sec: float = 10.0
    ) -> Dict[str, Any]:
        """Validates permission scopes and runs tool execution with concurrency timeouts."""
        start_time = time.perf_counter()
        logger.info("Tool Execution", tool=tool.name)
        
        try:
            # 1. Enforce safety check validation
            SafetyGuard.validate_execution(tool, params, user_permissions)
            
            # 2. Execute with thread timeout guard
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool.execute, params)
                raw_result = future.result(timeout=timeout_sec)
                
            serialized = tool.serialize_result(raw_result)
            duration = (time.perf_counter() - start_time) * 1000.0
            
            logger.info("Tool Result", tool=tool.name, status="success", duration_ms=duration)
            
            return {
                "tool_used": tool.name,
                "status": "success",
                "result": raw_result,
                "serialized": serialized,
                "execution_time_ms": duration
            }
            
        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000.0
            logger.error("Tool Execution Failed", tool=tool.name, error=str(exc), duration_ms=duration)
            return {
                "tool_used": tool.name,
                "status": "failed",
                "error": str(exc),
                "execution_time_ms": duration
            }
        finally:
            logger.info("Execution Complete")
