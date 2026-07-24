from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Any

class EvaluationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question: str
    answer: str
    overall_score: float
    category_scores: Dict[str, float]
    recommendations: List[str]
    metrics: Dict[str, Any]
