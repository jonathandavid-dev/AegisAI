import re
import math
from app.guardrails.hallucination_detector import HallucinationDetector

class EvaluationMetrics:
    """
    Houses metric calculations for RAG answers, document retrieval, and tool execution.
    """
    @staticmethod
    def evaluate_retrieval(retrieved_docs: list[str], expected_docs: list[str], latency_ms: float) -> dict:
        """
        Computes Top-K Recall, Precision, MRR, NDCG, and chunk coverage statistics.
        """
        if not expected_docs:
            return {
                "recall": 1.0, "precision": 1.0, "mrr": 1.0, "ndcg": 1.0,
                "coverage": 1.0, "latency_ms": latency_ms
            }
        if not retrieved_docs:
            return {
                "recall": 0.0, "precision": 0.0, "mrr": 0.0, "ndcg": 0.0,
                "coverage": 0.0, "latency_ms": latency_ms
            }

        retrieved_lower = [d.lower() for d in retrieved_docs]
        expected_lower = [d.lower() for d in expected_docs]

        matched = set(retrieved_lower) & set(expected_lower)
        recall = len(matched) / len(expected_lower)
        precision = len(matched) / len(retrieved_lower)

        mrr = 0.0
        for idx, doc in enumerate(retrieved_lower):
            if doc in expected_lower:
                mrr = 1.0 / (idx + 1)
                break

        dcg = 0.0
        for idx, doc in enumerate(retrieved_lower):
            rel = 1.0 if doc in expected_lower else 0.0
            dcg += rel / math.log2(idx + 2)

        idcg = 0.0
        for idx in range(min(len(expected_lower), len(retrieved_lower))):
            idcg += 1.0 / math.log2(idx + 2)

        ndcg = dcg / idcg if idcg > 0 else 0.0

        return {
            "recall": round(recall, 2),
            "precision": round(precision, 2),
            "mrr": round(mrr, 2),
            "ndcg": round(ndcg, 2),
            "coverage": round(recall, 2),
            "latency_ms": latency_ms
        }

    @staticmethod
    def evaluate_rag(
        answer: str,
        expected_answer: str,
        expected_keywords: list[str],
        citations: list,
        context_chunks: list[str]
    ) -> dict:
        """
        Computes Answer Correctness, Answer Completeness, Groundedness, relevance, and citation coverage.
        """
        if not answer:
            return {
                "correctness": 0.0, "completeness": 0.0, "groundedness": 0.0,
                "relevance": 0.0, "length": 0, "citation_coverage": 0.0
            }

        answer_lower = answer.lower()

        completed_count = 0
        if expected_keywords:
            for kw in expected_keywords:
                if kw.lower() in answer_lower:
                    completed_count += 1
            completeness = completed_count / len(expected_keywords)
        else:
            completeness = 1.0

        words_ans = set(re.findall(r'\b\w+\b', answer_lower))
        words_exp = set(re.findall(r'\b\w+\b', expected_answer.lower()))
        
        stopwords = {"the", "a", "an", "and", "or", "to", "is", "of", "in", "with", "for", "on", "at"}
        words_ans = words_ans - stopwords
        words_exp = words_exp - stopwords

        if words_ans or words_exp:
            intersect = words_ans & words_exp
            union = words_ans | words_exp
            correctness = len(intersect) / len(union) if union else 1.0
        else:
            correctness = 1.0

        hall_res = HallucinationDetector.detect_hallucinations(answer, context_chunks)
        groundedness = max(0.0, 1.0 - hall_res["score"])

        sentences = [s.strip() for s in re.split(r'[.!?]', answer) if s.strip()]
        cited_sentences = 0
        for sent in sentences:
            if re.search(r'\[\d+\]', sent):
                cited_sentences += 1
        citation_coverage = cited_sentences / len(sentences) if sentences else 0.0

        relevance = min(1.0, completeness * 1.2)

        return {
            "correctness": round(correctness, 2),
            "completeness": round(completeness, 2),
            "groundedness": round(groundedness, 2),
            "relevance": round(relevance, 2),
            "length": len(answer),
            "citation_coverage": round(citation_coverage, 2)
        }

    @staticmethod
    def evaluate_tool(tool_execution: dict | None, expected_tool: str | None = None) -> dict:
        """
        Evaluates tool selection, accuracy, execution latency, and success status.
        """
        if not tool_execution:
            return {
                "success": True,
                "tool_selected_correctly": True,
                "execution_success": True,
                "execution_latency_ms": 0.0,
                "fallback_success": False,
                "failure_reason": None,
                "score": 1.0
            }

        tool_used = tool_execution.get("tool_used")
        status = tool_execution.get("status", "success")
        latency = tool_execution.get("latency_ms", 0.0)
        fallback = tool_execution.get("fallback_used", False)
        error = tool_execution.get("error")

        tool_correct = True
        if expected_tool and tool_used != expected_tool:
            tool_correct = False

        exec_success = (status == "success")

        score = 1.0
        if not tool_correct:
            score -= 0.5
        if not exec_success:
            score -= 0.5
            if fallback:
                score += 0.25

        score = max(0.0, score)

        return {
            "success": exec_success,
            "tool_selected_correctly": tool_correct,
            "execution_success": exec_success,
            "execution_latency_ms": latency,
            "fallback_success": fallback,
            "failure_reason": error,
            "score": round(score, 2)
        }
