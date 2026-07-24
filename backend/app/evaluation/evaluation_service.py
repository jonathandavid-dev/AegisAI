import re
from app.guardrails.citation_validator import CitationValidator
from app.evaluation.scoring import QualityScorer
from app.evaluation.metrics import EvaluationMetrics
from app.quality.evaluation_result import EvaluationResult

class EvaluationService:
    """
    Evaluation orchestrator that triggers metric calculations from metrics.py.
    """
    @classmethod
    def evaluate_turn(
        cls,
        question: str,
        generated_answer: str,
        expected_answer: str,
        expected_keywords: list[str],
        retrieved_docs: list[str],
        expected_docs: list[str],
        citations: list,
        context_chunks: list[str],
        retrieval_latency_ms: float,
        total_latency_ms: float,
        tool_success: bool = True
    ) -> dict:
        """
        Runs evaluation on a conversation turn, compiling scores and recommendation logs.
        """
        ret_metrics = EvaluationMetrics.evaluate_retrieval(retrieved_docs, expected_docs, retrieval_latency_ms)
        rag_metrics = EvaluationMetrics.evaluate_rag(generated_answer, expected_answer, expected_keywords, citations, context_chunks)

        cit_res = CitationValidator.validate_citations(generated_answer, citations)
        citation_score = 1.0 if cit_res["success"] else 0.5
        if not citations and re.search(r'\[\d+\]', generated_answer):
            citation_score = 0.0

        latency_score = max(0.0, 1.0 - (max(0.0, total_latency_ms - 2000.0) / 8000.0))
        tool_success_score = 1.0 if tool_success else 0.0

        overall_res = QualityScorer.calculate_overall_score(
            retrieval_score=ret_metrics["recall"],
            groundedness_score=rag_metrics["groundedness"],
            citation_score=citation_score,
            correctness_score=rag_metrics["correctness"],
            tool_success_score=tool_success_score,
            latency_score=latency_score
        )

        eval_model = EvaluationResult(
            question=question,
            answer=generated_answer,
            overall_score=overall_res["overall_score"],
            category_scores=overall_res["category_scores"],
            recommendations=overall_res["recommendations"],
            metrics={
                "retrieval": ret_metrics,
                "rag": rag_metrics,
                "citations": cit_res,
                "latency_score": round(latency_score, 2),
                "total_latency_ms": total_latency_ms,
                "tool_success": tool_success
            }
        )

        return eval_model.model_dump()
