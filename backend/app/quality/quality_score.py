from pydantic import BaseModel, ConfigDict
from typing import Dict, List

class QualityScore(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    overall_score: float
    category_scores: Dict[str, float]
    recommendations: List[str]
