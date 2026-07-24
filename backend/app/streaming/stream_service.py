import time
import asyncio
import structlog
from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.chat.session_manager import SessionManager
from app.conversation.conversation_service import ConversationService
from app.conversation.history_service import HistoryService
from app.search.search_service import SearchService
from app.context.context_builder import ContextBuilder
from app.context.citation_builder import CitationBuilder
from app.llm.prompt_builder import PromptBuilder
from app.llm.llm_client import LLMClient
from app.storage.conversation_repository import ConversationRepository
from app.models.conversation import MessageRole
from app.agents.orchestrator import Orchestrator
from app.agents.execution_context import ExecutionContext
from app.streaming.sse_manager import SSEManager
from app.observability.tracing import trace_span
from app.observability.metrics import track_streaming_duration, track_tool_execution

logger = structlog.get_logger("aegis.stream")

class StreamService:
    """Orchestrates RAG pipelines and streams events chunk-by-chunk over SSE."""

    @staticmethod
    async def chat_stream(
        db: AsyncSession,
        question: str,
        account_id: int,
        workspace_id: int = 1,
        conversation_id: int | None = None,
        top_k: int = 5
    ) -> AsyncGenerator[str, None]:
        start_total = time.perf_counter()
        logger.info("Stream Chat Started", question=question, workspace_id=workspace_id)
        
        # Prompt validation
        from app.guardrails.guardrail_service import GuardrailService
        prompt_check = GuardrailService.check_prompt(question)
        if not prompt_check["success"]:
            yield SSEManager.format_event({
                "type": "done",
                "conversation_id": -1,
                "answer": f"Guardrail blocked: {prompt_check['reason']}",
                "citations": [],
                "retrieval": {"chunks_used": 0},
                "memory": {"summary_used": False, "messages_used": 0},
                "tool_execution": None,
                "timings": {},
                "processing_time_ms": 0.0
            })
            return

        yield SSEManager.format_event({"type": "progress", "stage": "start"})

        
        # Diagnostics details
        timings = {}
        tool_execution = None
        candidate_chunks = []
        selected_chunks = []
        citations = []
        rewritten_query = question
        summary = None
        active_history = []
        session = None

        with trace_span("Conversation", {"workspace_id": workspace_id, "account_id": account_id}) as conv_span:
            # 1. Load Conversation Session
            session = await SessionManager.get_or_create_session(db, conversation_id, account_id, workspace_id)
            
            # 2. Prepare Context (loads history, summarises, and rewrites query)
            prep_res = await ConversationService.prepare_context(db, session, question)
            rewritten_query = prep_res["rewritten_query"]
            summary = prep_res["summary"]
            active_history = prep_res["active_history"]
            
            yield SSEManager.format_event({
                "type": "progress",
                "stage": "context_preparation",
                "status": "completed",
                "rewritten_query": rewritten_query
            })
            
            # 3. Tool Orchestration execution step
            start_tool = time.perf_counter()
            exec_ctx = ExecutionContext(account_id=account_id, workspace_id=workspace_id)
            
            # Execute orchestrator tool checks inside Tool execution trace span
            with trace_span("Tool execution") as tool_span:
                orch_res = Orchestrator.execute_orchestration(rewritten_query, exec_ctx)
                
                tool_context = ""
                if orch_res.get("tool_execution") is not None:
                    exec_details = orch_res["tool_execution"]
                    tool_execution = {
                        "tool_used": exec_details["tool_used"],
                        "execution_time_ms": exec_details["execution_time_ms"],
                        "status": exec_details["status"]
                    }
                    if exec_details["status"] == "success":
                        tool_context = f"[Tool Context Output: {exec_details['tool_used']}]\n{exec_details['serialized']}"
                    
                    timings["tool_execution_ms"] = exec_details["execution_time_ms"]
                    track_tool_execution(exec_details["tool_used"], exec_details["status"])
                    
                    yield SSEManager.format_event({
                        "type": "progress",
                        "stage": "tool_execution",
                        "status": "completed",
                        "tool_used": exec_details["tool_used"],
                        "execution_time_ms": exec_details["execution_time_ms"]
                    })
            
            # 4. SearchService Retrieval
            intent = orch_res["intent"]
            
            if intent in ["RETRIEVAL", "HYBRID"] or not tool_execution:
                yield SSEManager.format_event({"type": "progress", "stage": "embedding", "status": "started"})
                # Yield embedding completion shortly after search retrieval executes
                yield SSEManager.format_event({"type": "progress", "stage": "embedding", "status": "completed"})
                
                yield SSEManager.format_event({"type": "progress", "stage": "retrieval", "status": "started"})
                
                start_ret = time.perf_counter()
                # Search performs internal tracing and caching
                search_res = await SearchService.search(
                    query=rewritten_query, 
                    top_k=top_k, 
                    similarity_threshold=0.50,
                    workspace_id=workspace_id
                )
                candidate_chunks = search_res.get("results", [])
                ret_duration = (time.perf_counter() - start_ret) * 1000.0
                timings["retrieval_ms"] = ret_duration
                
                yield SSEManager.format_event({
                    "type": "progress",
                    "stage": "retrieval",
                    "status": "completed",
                    "chunks_found": len(candidate_chunks)
                })

            # 5. Context Builder & Prompt Builder
            start_prompt = time.perf_counter()
            context_str, selected_chunks = ContextBuilder.build_context(candidate_chunks, max_chunks=top_k)
            combined_context = context_str
            if tool_execution and tool_context:
                combined_context = f"{tool_context}\n\n{context_str}".strip()
            
            history_context = HistoryService.format_history_for_prompt(active_history)
            prompt = PromptBuilder.build_prompt(combined_context, question, summary, history_context)
            timings["prompt_construction_ms"] = (time.perf_counter() - start_prompt) * 1000.0

            # 6. LLM Generation
            yield SSEManager.format_event({"type": "progress", "stage": "llm_generation", "status": "started"})
            
            start_llm = time.perf_counter()
            complete_answer = ""
            
            with trace_span("LLM") as llm_span:
                # Retrieve the asynchronous generator from LLM client
                token_gen = LLMClient.generate_stream(prompt)
                token_iter = token_gen.__aiter__()
                
                while True:
                    try:
                        # Heartbeat timeout guard
                        token = await asyncio.wait_for(
                            token_iter.__anext__(), 
                            timeout=settings.STREAM_HEARTBEAT_SECONDS
                        )
                        complete_answer += token
                        yield SSEManager.format_event({"type": "token", "content": token})
                    except asyncio.TimeoutError:
                        yield SSEManager.format_event({"type": "heartbeat"})
                    except StopAsyncIteration:
                        break
            
            llm_duration = (time.perf_counter() - start_llm) * 1000.0
            timings["llm_latency_ms"] = llm_duration
            
            # 7. Citation Builder & Guardrail checks
            citations = CitationBuilder.build_citations(selected_chunks)
            
            # Post-generation response guardrail check
            from app.guardrails.guardrail_service import GuardrailService
            context_texts = [c.get("content", "") for c in selected_chunks]
            resp_check = GuardrailService.check_response(complete_answer, citations, context_texts)
            if not resp_check["success"]:
                complete_answer = f"Guardrail blocked: {resp_check['reason']}"
                citations = []

            # Save conversations
            await ConversationRepository.create_message(db, session.id, account_id, workspace_id, MessageRole.USER, question)
            await ConversationRepository.create_message(db, session.id, account_id, workspace_id, MessageRole.ASSISTANT, complete_answer)
            logger.info("Stream Conversation Saved", conversation_id=session.id)


        # Trace Response streaming duration
        total_duration = (time.perf_counter() - start_total) * 1000.0
        timings["total_duration_ms"] = total_duration
        track_streaming_duration(total_duration / 1000.0)

        # Expose all performance timing diagnostics
        yield SSEManager.format_event({
            "type": "done",
            "conversation_id": session.id,
            "answer": complete_answer,
            "citations": citations,
            "retrieval": {
                "chunks_used": len(selected_chunks)
            },
            "memory": {
                "summary_used": summary is not None,
                "messages_used": len(active_history)
            },
            "tool_execution": tool_execution,
            "timings": timings,
            "processing_time_ms": total_duration
        })
