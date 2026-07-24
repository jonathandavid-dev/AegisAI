import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.evaluation import BenchmarkCase, EvaluationRun
from app.chat.chat_service import ChatService
from app.evaluation.evaluation_service import EvaluationService
from app.core.logging import app_logger

class BenchmarkRunner:
    """
    Coordinates and executes a suite of golden evaluation benchmark QA cases.
    """
    @classmethod
    async def run_suite(cls, db: AsyncSession, workspace_id: int, account_id: int) -> EvaluationRun:
        """
        Runs all benchmark cases registered in the database.
        """
        stmt = select(BenchmarkCase)
        res = await db.execute(stmt)
        cases = res.scalars().all()
        
        if not cases:
            app_logger.warning("no_benchmark_cases_found")
            empty_run = EvaluationRun(
                run_type="benchmark",
                overall_score=0.0,
                category_scores={
                    "retrieval": 0.0, "groundedness": 0.0, "citation": 0.0,
                    "correctness": 0.0, "tool_success": 0.0, "latency": 0.0
                },
                results=[]
            )
            db.add(empty_run)
            await db.commit()
            await db.refresh(empty_run)
            return empty_run

        results = []
        total_overall_score = 0.0
        
        sum_scores = {
            "retrieval": 0.0, "groundedness": 0.0, "citation": 0.0,
            "correctness": 0.0, "tool_success": 0.0, "latency": 0.0
        }

        for case in cases:
            start_time = time.perf_counter()
            
            try:
                chat_res = await ChatService.answer_question(
                    db=db,
                    question=case.question,
                    account_id=account_id,
                    workspace_id=workspace_id,
                    conversation_id=None,
                    top_k=5
                )
                
                total_latency = (time.perf_counter() - start_time) * 1000.0
                retrieval_latency = chat_res.get("processing_time_ms", total_latency) * 0.4
                
                citations = chat_res.get("citations", [])
                context_chunks = [c.get("text", "") for c in citations]
                retrieved_docs = list(set([c.get("filename", "") for c in citations if c.get("filename")]))
                
                tool_success = True
                if chat_res.get("tool_execution") and chat_res["tool_execution"].get("status") == "failed":
                    tool_success = False

                turn_eval = EvaluationService.evaluate_turn(
                    question=case.question,
                    generated_answer=chat_res.get("answer", ""),
                    expected_answer=case.expected_answer,
                    expected_keywords=case.expected_keywords or [],
                    retrieved_docs=retrieved_docs,
                    expected_docs=case.expected_documents or [],
                    citations=citations,
                    context_chunks=context_chunks,
                    retrieval_latency_ms=retrieval_latency,
                    total_latency_ms=total_latency,
                    tool_success=tool_success
                )
            except Exception as exc:
                app_logger.error("failed_to_evaluate_case", question=case.question, error=str(exc))
                turn_eval = {
                    "question": case.question,
                    "answer": f"Error running RAG turn: {str(exc)}",
                    "overall_score": 0.0,
                    "category_scores": {
                        "retrieval": 0.0, "groundedness": 0.0, "citation": 0.0,
                        "correctness": 0.0, "tool_success": 0.0, "latency": 0.0
                    },
                    "recommendations": [f"Execution failed: {str(exc)}"],
                    "metrics": {
                        "retrieval": {"recall": 0.0, "precision": 0.0},
                        "rag": {"correctness": 0.0, "groundedness": 0.0},
                        "citations": {"success": False, "broken_citations": []},
                        "latency_score": 0.0,
                        "total_latency_ms": 0.0,
                        "tool_success": False
                    }
                }

            results.append(turn_eval)
            total_overall_score += turn_eval["overall_score"]
            for cat in sum_scores:
                sum_scores[cat] += turn_eval["category_scores"].get(cat, 0.0)

        num_cases = len(cases)
        overall_score = total_overall_score / num_cases
        avg_scores = {cat: round(sum_val / num_cases, 2) for cat, sum_val in sum_scores.items()}

        run = EvaluationRun(
            run_type="benchmark",
            overall_score=round(overall_score, 2),
            category_scores=avg_scores,
            results=results
        )
        
        db.add(run)
        await db.commit()
        await db.refresh(run)
        
        app_logger.info("benchmark_suite_completed", run_id=run.id, overall_score=run.overall_score)
        return run
