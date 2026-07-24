from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class BenchmarkCase(Base):
    """
    SQLAlchemy model representing a golden benchmark evaluation case.
    """
    __tablename__ = "benchmark_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question: Mapped[str] = mapped_column(String, nullable=False)
    expected_answer: Mapped[str] = mapped_column(String, nullable=False)
    expected_sources: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    expected_documents: Mapped[list | None] = mapped_column(JSON, nullable=True)
    expected_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    ground_truth: Mapped[str] = mapped_column(String, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

class EvaluationRun(Base):
    """
    SQLAlchemy model representing a run of benchmark evaluations or ad-hoc checks.
    """
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "benchmark" or "single"
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    category_scores: Mapped[dict] = mapped_column(JSON, nullable=False)  # Dictionary of weighted subscores
    results: Mapped[list] = mapped_column(JSON, nullable=False)          # Individual case execution outcomes
    baseline_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
