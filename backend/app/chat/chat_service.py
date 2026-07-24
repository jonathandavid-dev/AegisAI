import time
import structlog
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
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

logger = structlog.get_logger("aegis.chat")

class ChatService:
    """Orchestrates multi-turn grounded RAG dialogues with enterprise tool execution chains and workspace isolation."""
    
    @staticmethod
    async def answer_question(
        db: AsyncSession,
        question: str,
        account_id: int,
        workspace_id: int = 1,
        conversation_id: int | None = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Runs the complete session loading, intent detection, planning, tool run, and response generation."""
        start_total = time.perf_counter()
        logger.info("Question Received", question=question, workspace_id=workspace_id)
        
        try:
            # 1. Load Conversation Session
            session = await SessionManager.get_or_create_session(db, conversation_id, account_id, workspace_id)
            
            # 2. Prepare Context (loads history, summarises, and rewrites query)
            prep_res = await ConversationService.prepare_context(db, session, question)
            rewritten_query = prep_res["rewritten_query"]
            summary = prep_res["summary"]
            active_history = prep_res["active_history"]
            
            # Format active history text
            history_context = HistoryService.format_history_for_prompt(active_history)
            
            # 3. Tool Orchestration execution step
            exec_ctx = ExecutionContext(account_id=account_id, workspace_id=workspace_id)
            orch_res = Orchestrator.execute_orchestration(rewritten_query, exec_ctx)
            
            tool_execution = None
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
            
            # 4. SearchService Retrieval
            logger.info("Search Started")
            start_ret = time.perf_counter()
            intent = orch_res["intent"]
            candidate_chunks = []
            
            # Execute retrieval only if the intent calls for retrieval, hybrid, or if no tool succeeded
            if intent in ["RETRIEVAL", "HYBRID"] or not tool_execution:
                search_res = await SearchService.search(
                    query=rewritten_query, 
                    top_k=top_k, 
                    similarity_threshold=0.50,
                    workspace_id=workspace_id
                )
                candidate_chunks = search_res.get("results", [])
            ret_duration = (time.perf_counter() - start_ret) * 1000.0
            logger.info("Search Completed", duration_ms=ret_duration, chunks_found=len(candidate_chunks))
            
            # 5. Context Builder
            context_str, selected_chunks = ContextBuilder.build_context(candidate_chunks, max_chunks=top_k)
            
            # Merge tool output and document contexts
            combined_context = context_str
            if tool_context:
                combined_context = f"{tool_context}\n\n{context_str}".strip()
            
            # 6. Prompt Builder
            logger.info("Prompt Built")
            prompt = PromptBuilder.build_prompt(combined_context, question, summary, history_context)
            
            # 7. LLM Generation
            logger.info("LLM Started")
            start_llm = time.perf_counter()
            answer = LLMClient.generate(prompt)
            llm_duration = (time.perf_counter() - start_llm) * 1000.0
            logger.info("LLM Finished", duration_ms=llm_duration)
            
            # 8. Citation Builder
            citations = CitationBuilder.build_citations(selected_chunks)
            
            # 9. Persist Messages
            await ConversationRepository.create_message(db, session.id, account_id, workspace_id, MessageRole.USER, question)
            await ConversationRepository.create_message(db, session.id, account_id, workspace_id, MessageRole.ASSISTANT, answer)
            logger.info("Conversation Saved", conversation_id=session.id)
            
            total_duration = (time.perf_counter() - start_total) * 1000.0
            logger.info("Total Request Time", total_duration_ms=total_duration)
            
            return {
                "conversation_id": session.id,
                "question": question,
                "rewritten_query": rewritten_query,
                "answer": answer,
                "citations": citations,
                "retrieval": {
                    "chunks_used": len(selected_chunks)
                },
                "memory": {
                    "summary_used": summary is not None,
                    "messages_used": len(active_history)
                },
                "tool_execution": tool_execution,
                "processing_time_ms": total_duration
            }
            
        except Exception as exc:
            total_duration = (time.perf_counter() - start_total) * 1000.0
            logger.error("Chat Failed", error=str(exc), duration_ms=total_duration)
            raise exc
