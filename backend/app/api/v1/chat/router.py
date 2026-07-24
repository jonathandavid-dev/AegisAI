from typing import Any
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.schemas.chat import ChatRequest, ChatResponse
from app.chat.chat_service import ChatService
from app.security.permissions import PermissionChecker
from app.audit.audit_service import AuditService
from app.tenancy.tenant_context import TenantContext
from app.tenancy.tenant_guard import get_tenant_context, WorkspacePermissionChecker

router = APIRouter()

@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def perform_chat(
    request: ChatRequest,
    request_http: Request,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> Any:
    """Orchestrates RAG pipeline to answer the user question using database-backed message history with workspace isolation."""
    if request.stream:
        from fastapi.responses import StreamingResponse
        from app.streaming.stream_service import StreamService
        
    # Log CHAT audit event for stream request initiation
    from app.guardrails.guardrail_service import GuardrailService
    from fastapi import HTTPException
    
    # Pre-generation prompt guardrail
    prompt_check = GuardrailService.check_prompt(request.question)
    if not prompt_check["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=prompt_check["reason"]
        )

    if request.stream:
        from fastapi.responses import StreamingResponse
        from app.streaming.stream_service import StreamService
        
        await AuditService.log_event(
            db=db,
            account_id=current_account.id,
            workspace_id=tenant_context.workspace.id,
            action="CHAT",
            resource="conversation",
            resource_id="streaming_initiated",
            ip_address=request_http.client.host if request_http.client else None,
            user_agent=request_http.headers.get("user-agent")
        )
        
        return StreamingResponse(
            StreamService.chat_stream(
                db=db,
                question=request.question,
                account_id=current_account.id,
                workspace_id=tenant_context.workspace.id,
                conversation_id=request.conversation_id,
                top_k=request.top_k
            ),
            media_type="text/event-stream"
        )

    results = await ChatService.answer_question(
        db=db,
        question=request.question,
        account_id=current_account.id,
        workspace_id=tenant_context.workspace.id,
        conversation_id=request.conversation_id,
        top_k=request.top_k
    )

    # Post-generation response guardrail
    context_texts = [c.get("text", "") for c in results.get("citations", [])]
    resp_check = GuardrailService.check_response(
        results.get("answer", ""),
        results.get("citations", []),
        context_texts
    )
    if not resp_check["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resp_check["reason"]
        )

    # 1. Log CHAT audit event
    await AuditService.log_event(
        db=db,
        account_id=current_account.id,
        workspace_id=tenant_context.workspace.id,
        action="CHAT",
        resource="conversation",
        resource_id=str(results["conversation_id"]),
        ip_address=request_http.client.host if request_http.client else None,
        user_agent=request_http.headers.get("user-agent")
    )
    
    # 2. Log TOOL_EXECUTION audit event if a tool was executed
    if results.get("tool_execution") is not None:
        await AuditService.log_event(
            db=db,
            account_id=current_account.id,
            workspace_id=tenant_context.workspace.id,
            action="TOOL_EXECUTION",
            resource="tool",
            resource_id=results["tool_execution"]["tool_used"],
            ip_address=request_http.client.host if request_http.client else None,
            user_agent=request_http.headers.get("user-agent"),
            metadata_json=results["tool_execution"]
        )
        
    return results

