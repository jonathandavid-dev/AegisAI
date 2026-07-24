class QualityScorer:
    """
    Computes a weighted overall AI Quality Score based on:
    - Retrieval Quality (25%)
    - Groundedness (25%)
    - Citation Accuracy (20%)
    - Answer Correctness (15%)
    - Tool Success (10%)
    - Latency (5%)
    """
    WEIGHTS = {
        "retrieval": 0.25,
        "groundedness": 0.25,
        "citation": 0.20,
        "correctness": 0.15,
        "tool_success": 0.10,
        "latency": 0.05
    }

    @classmethod
    def calculate_overall_score(
        cls,
        retrieval_score: float,
        groundedness_score: float,
        citation_score: float,
        correctness_score: float,
        tool_success_score: float,
        latency_score: float
    ) -> dict:
        """
        Computes weighted overall score and generates tailored quality recommendations.
        """
        overall = (
            retrieval_score * cls.WEIGHTS["retrieval"] +
            groundedness_score * cls.WEIGHTS["groundedness"] +
            citation_score * cls.WEIGHTS["citation"] +
            correctness_score * cls.WEIGHTS["correctness"] +
            tool_success_score * cls.WEIGHTS["tool_success"] +
            latency_score * cls.WEIGHTS["latency"]
        )

        recommendations = []
        if retrieval_score < 0.70:
            recommendations.append("Retrieval quality is low. Try increasing Top-K, refining chunk sizes, or improving query embeddings.")
        if groundedness_score < 0.75:
            recommendations.append("Groundedness is low. LLM is generating claims not backed by documents. Adjust temperature or enforce formatting.")
        if citation_score < 0.90:
            recommendations.append("Citation accuracy is low. Fix fabricated or adjacent duplicate references in prompt templates.")
        if correctness_score < 0.70:
            recommendations.append("Answer correctness is low. The response differs significantly from ground truth. Refine grounding instructions.")
        if tool_success_score < 0.80:
            recommendations.append("Tool success rate is low. Check fallback configurations and tool parameter definitions.")
        if latency_score < 0.60:
            recommendations.append("Response latency is high. Consider adding caching, optimizing DB indexes, or upgrading LLM hosting tiers.")

        if not recommendations:
            recommendations.append("Excellent response quality! All systems meeting target SLAs.")

        return {
            "overall_score": round(overall, 2),
            "category_scores": {
                "retrieval": round(retrieval_score, 2),
                "groundedness": round(groundedness_score, 2),
                "citation": round(citation_score, 2),
                "correctness": round(correctness_score, 2),
                "tool_success": round(tool_success_score, 2),
                "latency": round(latency_score, 2)
            },
            "recommendations": recommendations
        }
