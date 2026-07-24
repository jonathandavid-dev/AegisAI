import contextvars
from typing import Any, Dict

# Context variables to track across request boundaries
correlation_id_ctx = contextvars.ContextVar("correlation_id", default=None)
workspace_id_ctx = contextvars.ContextVar("workspace_id", default=None)
account_id_ctx = contextvars.ContextVar("account_id", default=None)
conversation_id_ctx = contextvars.ContextVar("conversation_id", default=None)
request_path_ctx = contextvars.ContextVar("request_path", default=None)
duration_ms_ctx = contextvars.ContextVar("duration_ms", default=None)

def bind_observability_fields(
    correlation_id: Any = None,
    workspace_id: Any = None,
    account_id: Any = None,
    conversation_id: Any = None,
    request_path: Any = None,
    duration_ms: Any = None
) -> None:
    """Binds request identifiers to thread-local contexts."""
    if correlation_id is not None:
        correlation_id_ctx.set(correlation_id)
    if workspace_id is not None:
        workspace_id_ctx.set(workspace_id)
    if account_id is not None:
        account_id_ctx.set(account_id)
    if conversation_id is not None:
        conversation_id_ctx.set(conversation_id)
    if request_path is not None:
        request_path_ctx.set(request_path)
    if duration_ms is not None:
        duration_ms_ctx.set(duration_ms)

def clear_observability_fields() -> None:
    """Resets all context variables for the current request scope."""
    correlation_id_ctx.set(None)
    workspace_id_ctx.set(None)
    account_id_ctx.set(None)
    conversation_id_ctx.set(None)
    request_path_ctx.set(None)
    duration_ms_ctx.set(None)

def observability_processor(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Structlog processor ensuring standardized enterprise tracking metadata exist in every message."""
    event_dict["correlation_id"] = correlation_id_ctx.get()
    event_dict["workspace_id"] = workspace_id_ctx.get()
    event_dict["account_id"] = account_id_ctx.get()
    event_dict["conversation_id"] = conversation_id_ctx.get()
    event_dict["request_path"] = request_path_ctx.get()
    event_dict["duration_ms"] = duration_ms_ctx.get()
    return event_dict
